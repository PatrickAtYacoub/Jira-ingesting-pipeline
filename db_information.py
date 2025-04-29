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
    SELECT key, status_category, assignee FROM jira_issue;
    """
)

if res is None:
    print("Table does not exist. Creating table...")
else:
    print(f"Found {len(res)} records in the 'jira_issue' table.")
    sorted_keys = sorted(res, key=lambda x: x[1])
    for key in sorted_keys:
        print(f"{key[0]} is assigned to {key[2]} with status category {key[1]}")


print()


res_subtask_keys = client.execute_sql(
    """
    SELECT key, parent_key, assignee FROM jira_subtask;
    """
)
if res_subtask_keys is None:
    print("Table 'jira_subtask' does not exist.")
else:
    print(f"Found {len(res_subtask_keys)} records in the 'jira_subtask' table.")
    sorted_subtask_keys = sorted(res_subtask_keys, key=lambda x: x[2])
    for key in sorted_subtask_keys:
        print(f"{key[0]} is a subtask of {key[1]} assigned to {key[2]}")
