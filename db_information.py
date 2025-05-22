"""
This module contains functions to create and drop tables in the database.
It uses the `VectorDB` class to execute SQL commands for creating and dropping 
tables related to Jira issues and subtasks.
It also includes logging to track the success or failure of these operations.
"""

import os
from dotenv import load_dotenv
from db import VectorDB, DBConfig
import json

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

res = client.describe_database()
print(json.dumps(res, indent=4))