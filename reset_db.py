"""
This module contains functions to create and drop tables in the database.
It uses the `VectorDB` class to execute SQL commands for creating and dropping 
tables related to Jira issues and subtasks.
It also includes logging to track the success or failure of these operations.
"""

import os
from dotenv import load_dotenv

from db.create_tables import create_jira_tables, drop_jira_tables
from db.vectordb_client import VectorDB, DBConfig

load_dotenv()

PG_PWD = os.getenv("PG_PWD")

if PG_PWD is None:
    raise ValueError("PG_PWD environment variable is not set.")

client = VectorDB(
    DBConfig(
        dbname="hackathon_ofa",
        user="hackathon_ofa",
        password=PG_PWD,
        host="hackathon-ofa.postgres.database.azure.com"
    )
)
drop_jira_tables(client)
create_jira_tables(client)

print(client.describe_database())
