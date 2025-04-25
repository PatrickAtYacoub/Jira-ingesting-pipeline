import logging
from db.vectordb_client import VectorDB
from db.query_store import QueryStore

logging.basicConfig(level=logging.INFO)


def create_jira_tables(client: VectorDB):
    """
    Creates the tables necessary for storing Jira issues and subtasks.
    """
    try:
        logging.info("Creating jira_issue table...")
        sql_issue = QueryStore.get_sql("create_jira_issue_table")
        client.execute_sql(sql_issue)

        logging.info("Creating jira_subtask table...")
        sql_subtask = QueryStore.get_sql("create_jira_subtask_table")
        client.execute_sql(sql_subtask)

        logging.info("All Jira tables created successfully.")
    except Exception as e:
        logging.error(f"Error while creating Jira tables: {e}")

def drop_jira_tables(client: VectorDB):
    """
    Drops the tables for Jira issues and subtasks.
    """
    try:
        logging.info("Dropping jira_issue table...")
        sql_issue = QueryStore.get_sql("drop_jira_issue_table")
        client.execute_sql(sql_issue)

        logging.info("Dropping jira_subtask table...")
        sql_subtask = QueryStore.get_sql("drop_jira_subtask_table")
        client.execute_sql(sql_subtask)

        logging.info("All Jira tables dropped successfully.")
    except Exception as e:
        logging.error(f"Error while dropping Jira tables: {e}")