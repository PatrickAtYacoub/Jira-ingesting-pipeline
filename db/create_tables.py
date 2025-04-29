"""
This module contains functions to create and drop tables in the database.
It uses the `VectorDB` class to execute SQL commands for creating and dropping 
tables related to Jira issues and subtasks.
It also includes logging to track the success or failure of these operations.
"""

from db.vectordb_client import VectorDB
from db.query_store import QueryStore
from logger import logger

def create_jira_tables(client: VectorDB):
    """
    Creates the tables necessary for storing Jira issues and subtasks.
    """
    try:
        logger.info("Creating jira_issue table...")
        sql_issue = QueryStore.get_sql("create_jira_issue_table")
        client.execute_sql(sql_issue)

        logger.info("Creating jira_subtask table...")
        sql_subtask = QueryStore.get_sql("create_jira_subtask_table")
        client.execute_sql(sql_subtask)

        logger.info("Creating jira_task table...")
        sql_task = QueryStore.get_sql("create_jira_task_table")
        client.execute_sql(sql_task)

        logger.info("Creating jira_bug table...")
        sql_bug = QueryStore.get_sql("create_jira_bug_table")
        client.execute_sql(sql_bug)

        logger.info("All Jira tables created successfully.")
    except KeyError as e:
        logger.error("SQL query key not found: %s", e)
    except ConnectionError as e:
        logger.error("Database connection error: %s", e)
    except RuntimeError as e:
        logger.error("Runtime error while creating Jira tables: %s", e)

def drop_jira_tables(client: VectorDB):
    """
    Drops the tables for Jira issues and subtasks.
    """
    try:
        logger.info("Dropping jira_subtask table...")
        sql_subtask = QueryStore.get_sql("drop_jira_subtask_table")
        client.execute_sql(sql_subtask)

        logger.info("Dropping jira_issue table...")
        sql_issue = QueryStore.get_sql("drop_jira_issue_table")
        client.execute_sql(sql_issue)

        logger.info("Dropping jira_task table...")
        sql_task = QueryStore.get_sql("drop_jira_task_table")
        client.execute_sql(sql_task)

        logger.info("Dropping jira_bug table...")
        sql_bug = QueryStore.get_sql("drop_jira_bug_table")
        client.execute_sql(sql_bug)

        logger.info("All Jira tables dropped successfully.")
    except KeyError as e:
        logger.error("SQL query key not found: %s", e)
    except ConnectionError as e:
        logger.error("Database connection error: %s", e)
    except RuntimeError as e:
        logger.error("Runtime error while dropping Jira tables: %s", e)
