"""
This module contains functions to create and drop tables in the database.
It uses the `VectorDB` class to execute SQL commands for creating and dropping 
tables related to Jira issues and subtasks.
It also includes logging to track the success or failure of these operations.
"""

import os
from dotenv import load_dotenv
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

res = client.execute_sql(
    """
    SELECT COUNT(*) FROM jira_issue;
    """
)

if res is None:
    print("Table does not exist. Creating table...")
else:
    print(f"Found {res[0][0]} records in the table.")

res_subtask = client.execute_sql(
    """
    SELECT COUNT(*) FROM jira_subtask;
    """
)

if res_subtask is None:
    print("Table 'jira_subtask' does not exist.")
else:
    print(f"Found {res_subtask[0][0]} records in the 'jira_subtask' table.")
