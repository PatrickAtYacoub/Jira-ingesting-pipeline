from db.create_tables import create_jira_tables, drop_jira_tables
from db.vectordb_client import VectorDB
import os
from dotenv import load_dotenv

load_dotenv()

PG_PWD = os.getenv("PG_PWD")

if PG_PWD is None:
    raise ValueError("PG_PWD environment variable is not set.")

client = VectorDB(
    dbname="hackathon_ofa",
    user="hackathon_ofa",
    password=PG_PWD,    
    host="hackathon-ofa.postgres.database.azure.com"
)
drop_jira_tables(client)
create_jira_tables(client)

print(client.describe_database())