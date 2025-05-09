"""
vectordb_client.py

This module provides a class, VectorDB, for interacting with a PostgreSQL database
to store and retrieve text embeddings. It includes functionality for setting up the
database, creating embeddings using an Azure OpenAI model, storing embeddings, and
retrieving similar texts based on vector similarity.

Features:
- Dependency injection for the embedding model.
- Parameterized vector dimensions.
- Resource management for database connections.
- Logging for better traceability.
- Error handling for robustness.

Author: Patrick Scheich
Date: 2025-03-28
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv
import psycopg2
from openai import AzureOpenAI
from pgvector.psycopg2 import register_vector

from db.query_store import QueryStore

from lib.logger import logger


@dataclass
class DBConfig:
    """
    Configuration class for the database connection.
    Attributes:
        dbname (str): The name of the database.
        user (str): The username for the database connection.
        password (str): The password for the database connection.
        host (str): The host address of the database.
        port (int): The port number for the database connection (optional).
        embedding_model (object): The embedding model to use (optional).
        vector_dim (int): The dimension of the vector embeddings (default is 3072).
    """

    dbname: str
    user: str
    password: str
    host: str
    port: int = None
    embedding_model: object = None
    vector_dim: int = 3072


class VectorDB:
    """
    A class for interacting with a PostgreSQL database to store and retrieve text embeddings.
    Improvements:
      - Explicit setup workflow instead of too many initializations in the constructor.
      - Logging instead of direct print statements.
      - Error handling using try/except.
      - Use of dependency injection for the embedding model.
      - Parameterization of vector dimension.
      - Careful handling of resources (connections, cursors).
    """

    def __init__(self, config: DBConfig):
        # Validierung und Initialisierung der Konfiguration
        load_dotenv()
        if not config.dbname.isidentifier():
            raise ValueError("The database name must be a valid identifier.")
        self.dbname = config.dbname
        self.user = config.user
        self.password = config.password
        self.host = config.host
        self.port = config.port
        self.vector_dim = config.vector_dim

        self.embedding_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        if not self.embedding_api_key:
            raise ValueError(
                "The OpenAI API key for embedding model is not set in the environment variables."
            )
        self.base_url = "https://oai-hackathon-ofa.openai.azure.com/"
        self.instance_name = "oai-hackathon-ofa"
        self.api_version = "2024-02-01"

        if config.embedding_model is None:
            self.embedding_model = AzureOpenAI(
                api_version=self.api_version,
                azure_endpoint=self.base_url,
                api_key=self.embedding_api_key,
            )
        else:
            self.embedding_model = config.embedding_model

        self.conn = None
        self.cursor = None
        self._connect_to_postgres()
        register_vector(self.conn)

    def setup(self):
        """
        Sets up the necessary connections and database configurations.
        This method performs the following steps:
        1. Connects to the PostgreSQL database.
        2. Creates the database if it does not exist.
        3. Connects to the vector database.
        4. Creates the required extension and table in the vector database.
        Raises:
            Exception: If any error occurs during the setup process,
                it logs the error and raises the exception.
        """
        try:
            self._connect_to_postgres()
        except psycopg2.OperationalError as e:
            logger.error("Operational error during PostgreSQL connection: %s", e)
            raise

        try:
            self._create_extension_and_table()
        except psycopg2.Error as e:
            logger.error("Error creating extension or table: %s", e)
            raise

    def create_embedding(self, text: str):
        """
        Creates an embedding for the given text using the specified embedding model.
        Args:
            text (str): The text to be embedded.
        Returns:
            list: The embedding vector for the text.
        Raises:
            ValueError: If the text is empty or None.
        """
        if not text or not isinstance(text, str):
            logger.error("Invalid text input: %s", text)

        embedding = self.embedding_model.embeddings.create(
            model="text-embedding-3-large",
            input=[
                text,
            ],
            dimensions=1024,
        )

        return embedding.data[0].embedding

    def _connect_to_postgres(self):
        """
        Establishes a connection to a PostgreSQL database using the provided
        credentials and connection parameters.
        This method sets up a connection to the PostgreSQL database specified
        by the instance attributes dbname, user, password, host, and port.
        It also enables autocommit mode and initializes a cursor for executing
        SQL queries.
        Raises:
            psycopg2.OperationalError: If the connection to the database fails.
        """
        try:
            if self.port:
                self.conn = psycopg2.connect(
                    dbname="postgres",
                    user=self.user,
                    password=self.password,
                    host=self.host,
                    port=self.port,
                )
            else:
                self.conn = psycopg2.connect(
                    dbname=self.dbname,
                    user=self.user,
                    password=self.password,
                    host=self.host,
                )
                self.conn.autocommit = True
                self.cursor = self.conn.cursor()
                # self.is_connected = True
                logger.info(
                    "Connection to the 'postgres' database successfully established."
                )
        except psycopg2.OperationalError as e:
            logger.error("OperationalError: Unable to connect to 'postgres': %s", e)
            raise
        except psycopg2.InterfaceError as e:
            logger.error("InterfaceError: Issue with the database interface: %s", e)
            raise
        except psycopg2.DatabaseError as e:
            logger.error("DatabaseError: General database error occurred: %s", e)
            raise

    def _create_extension_and_table(self):
        """
        Creates the necessary extension and table for storing embeddings.

        This method ensures that the 'vector' extension and the 'vectors' table
        are created in the database if they do not already exist.
        Raises:
            psycopg2.Error: If an error occurs while creating the extension or table.
        """
        try:
            self.cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            self.conn.commit()
            logger.info("Extension has been created or already exists.")
        except psycopg2.ProgrammingError as e:
            logger.error("ProgrammingError while creating extension: %s", e)
            self.conn.rollback()
            raise
        except psycopg2.IntegrityError as e:
            logger.error("IntegrityError while creating extension: %s", e)
            self.conn.rollback()
            raise
        except psycopg2.DatabaseError as e:
            logger.error("DatabaseError while creating extension: %s", e)
            self.conn.rollback()
            raise

    def store_text(self, statement_name, **columns):
        """
        Stores the text in the database using the provided SQL statement name and parameters.
        Args:
            statement_name (str): The name of the SQL statement to execute.
            **columns: The parameters to be passed to the SQL statement.
        Raises:
            psycopg2.Error: If an error occurs while executing the SQL statement.
                """
        # if not self.is_connected:
        #     raise RuntimeError("Database connection is not established. Call setup() first.")
        sql_statement = QueryStore.get_sql(statement_name, **columns)
        try:
            self.cursor.execute(sql_statement)
            self.conn.commit()
            logger.info("Text stored successfully.")
        except psycopg2.ProgrammingError as e:
            logger.error("ProgrammingError while storing text: %s", e)
            self.conn.rollback()
            raise
        except psycopg2.IntegrityError as e:
            logger.error("IntegrityError while storing text: %s", e)
            self.conn.rollback()
            raise
        except psycopg2.DatabaseError as e:
            logger.error("DatabaseError while storing text: %s", e)
            self.conn.rollback()
            raise

    def get_matches(self, query, query_statement_name, limit=3):
        """
        Finds the most similar texts to the given query based on their embeddings.
        Args:
            query (str): The query text for which to find similar texts.
            limit (int): The maximum number of similar texts to return.
        Returns:
            results (list): A list of tuples containing the text and similarity score.
        Raises:
            psycopg2.Error: If an error occurs while executing the database query.
        """
        query_embedding = self.create_embedding(query)  # This returns a list/array

        sql_statement = QueryStore.get_sql(
            query_statement_name, vector=query_embedding, limit=limit
        )
        logger.debug("SQL statement: %s", sql_statement)

        try:
            self.cursor.execute(sql_statement)
            results = self.cursor.fetchall()
            return results
        except psycopg2.ProgrammingError as e:
            logger.error("ProgrammingError while retrieving matches: %s", e)
            raise
        except psycopg2.IntegrityError as e:
            logger.error("IntegrityError while retrieving matches: %s", e)
            raise
        except psycopg2.DatabaseError as e:
            logger.error("DatabaseError while retrieving matches: %s", e)
            raise

    def close(self):
        """
        Closes the cursor and database connection.
        """
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
            # self.is_connected = False
            logger.info("Database connection closed.")
        except psycopg2.InterfaceError as e:
            logger.error("InterfaceError while closing resources: %s", e)
        except psycopg2.DatabaseError as e:
            logger.error("DatabaseError while closing resources: %s", e)
        except (psycopg2.Error, RuntimeError) as e:
            logger.error("Error while closing resources: %s", e)

    def describe_database(self):
        """
        Describes the database by listing the tables and extensions.
        Returns:
            list of all tables and extensions in the database: {
                tables: [
                    table_name: str,
                    columns: [
                        column_name: str,
                        data_type: str
                    ]
                ],
                extensions: [
                    extension_name: str
                ]}
        Raises:
            psycopg2.Error: If an error occurs while describing the database.
        """
        try:
            self.cursor.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
            )
            tables = [table[0] for table in self.cursor.fetchall()]
            self.cursor.execute("SELECT extname FROM pg_extension")
            extensions = [extension[0] for extension in self.cursor.fetchall()]

            table_details = []
            for table in tables:
                self.cursor.execute(
                    f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = '{table}'
                """
                )
                columns = self.cursor.fetchall()
                table_details.append({"table_name": table, "columns": columns})
            return {"tables": table_details, "extensions": extensions}

        except psycopg2.ProgrammingError as e:
            logger.error("ProgrammingError while describing the database: %s", e)
            self.conn.rollback()
            raise
        except psycopg2.InterfaceError as e:
            logger.error("InterfaceError while describing the database: %s", e)
            raise
        except psycopg2.DatabaseError as e:
            logger.error("DatabaseError while describing the database: %s", e)
            raise

    def execute_sql(self, sql_statement, **sql_params):
        """
        Executes a given SQL statement.
        Args:
            sql_statement (str): The SQL statement to execute.
        Raises:
            psycopg2.Error: If an error occurs while executing the SQL statement.
        """

        if " " not in sql_statement.strip():
            logger.debug(
                "SQL statement appears to be a key. Attempting to retrieve from QueryStore."
            )
            sql_statement = QueryStore.get_sql(sql_statement, **sql_params)
        try:
            self.cursor.execute(sql_statement)
            if sql_statement.strip().lower().startswith("select"):
                result = self.cursor.fetchall()
                logger.info("SQL SELECT statement executed successfully.")
                return result
            self.conn.commit()
            logger.info("SQL statement executed successfully.")
            return None
        except psycopg2.ProgrammingError as e:
            logger.error("ProgrammingError while executing SQL statement: %s", e)
            self.conn.rollback()
            raise
        except psycopg2.IntegrityError as e:
            logger.error("IntegrityError while executing SQL statement: %s", e)
            self.conn.rollback()
            raise
        except psycopg2.DatabaseError as e:
            logger.error("DatabaseError while executing SQL statement: %s", e)
            self.conn.rollback()
            raise


def format_output(string: str) -> str:
    """
    Formats the output string by replacing escape sequences with actual characters.
    Returns the formatted string.
    """
    formatted_res = string.replace("\\r\\n", "\n")
    formatted_res = formatted_res.replace("\\r\\r", "\n")
    return formatted_res.replace("\\n", "\n")


if __name__ == "__main__":
    PG_PWD = os.getenv("PG_PWD")
    client = VectorDB(
        DBConfig(
            dbname="hackathon_ofa",
            user="hackathon_ofa",
            password=PG_PWD,
            host="hackathon-ofa.postgres.database.azure.com",
        )
    )

    descr = client.describe_database()

    res = client.get_matches("My computer does not boot", "query_servicedesk", limit=3)
