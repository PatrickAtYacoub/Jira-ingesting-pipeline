"""
This module contains parameterized tools to query JIRA data from the database.
Each tool is responsible for querying a specific column from a defined table using safe SQL construction.
"""

import sys
from config import Config
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from langchain_openai import AzureChatOpenAI
from db.vectordb_client import VectorDB, DBConfig
from lib.logger import agent_logger as logger

checkpointer = InMemorySaver()
store = InMemoryStore()

config = Config.load_from_env()

model = AzureChatOpenAI(
    azure_deployment="gpt-4o-mini",
    azure_endpoint=config.openai_base_url,
    api_version=config.openai_api_version,
    model_name="gpt-4o-mini"
)

db_client = VectorDB(
    DBConfig(
        dbname=config.pg_dbname,
        user=config.pg_user,
        password=config.pg_password,
        host=config.pg_host
    )
)

# --- Parameterized Tools ---

def get_tasks_by_assignee(assignee: str):
    """
    Retrieves tasks assigned to a specific assignee from the 'jira_task' table,
    excluding vector fields.

    Args:
        assignee (str): The username or identifier of the assignee.

    Returns:
        list: A list of task dictionaries with fields: key, parent_key, summary, 
              description, issue_type, status, status_category, project, assignee, 
              reporter, created, updated, time_spent_seconds, and url.
    """
    sql = f"""
    SELECT key, parent_key, summary, description, issue_type, status, 
           status_category, project, assignee, reporter, created, updated, 
           time_spent_seconds, url 
    FROM jira_task 
    WHERE assignee = '{assignee}'
    """
    return get_issues_from_db(sql)


def get_tasks_by_project(project: str):
    """
    Retrieves tasks for a given project from the 'jira_task' table,
    excluding vector fields.

    Args:
        project (str): The project name or identifier.

    Returns:
        list: A list of task dictionaries with the same field key, parent_key, summary, 
              description, issue_type, status, status_category, project, assignee, 
              reporter, created, updated, time_spent_seconds, and url.
    """
    sql = f"""
    SELECT key, parent_key, summary, description, issue_type, status, 
           status_category, project, assignee, reporter, created, updated, 
           time_spent_seconds, url 
    FROM jira_task 
    WHERE project = '{project}'
    """
    return get_issues_from_db(sql)


def get_bugs_by_status(status: str):
    """
    Retrieves bugs from the 'jira_bug' table filtered by status,
    excluding vector fields.

    Args:
        status (str): The bug status to filter by (e.g., "Open", "Closed").

    Returns:
        list: A list of bug dictionaries with fields: key, summary, description, 
              issue_type, status, status_category, project, assignee, reporter, 
              created, updated, time_spent_seconds, and url.
    """
    sql = f"""
    SELECT key, summary, description, issue_type, status, 
           status_category, project, assignee, reporter, created, 
           updated, time_spent_seconds, url 
    FROM jira_bug 
    WHERE status = '{status}'
    """
    return get_issues_from_db(sql)


def get_subtasks_by_parent_key(parent_key: str):
    """
    Retrieves subtasks for a specific parent issue from the 'jira_subtask' table,
    excluding vector fields.

    Args:
        parent_key (str): The key of the parent issue.

    Returns:
        list: A list of subtask dictionaries with fields: key, parent_key, summary, 
              status, status_category, assignee, created, updated, 
              time_spent_seconds, and url.
    """
    sql = f"""
    SELECT key, parent_key, summary, status, 
           status_category, assignee, created, updated, 
           time_spent_seconds, url 
    FROM jira_subtask 
    WHERE parent_key = '{parent_key}'
    """
    return get_issues_from_db(sql)


def get_tasks_by_description_similarity(text: str):
    """
    Retrieves the top 5 tasks with the most similar descriptions (vector-based match),
    but returns all metadata fields excluding vectors.

    Args:
        text (str): Input text to compare against description vectors.

    Returns:
        list: Top 5 most similar task with the following fields: key, parent_key, summary,
              description, issue_type, status, status_category, project, assignee, 
              reporter, created, updated, time_spent_seconds, and url.
    """
    res = []
    embedding = db_client.create_embedding(text)
    sql = f"""
    SELECT key, parent_key, summary, description, issue_type, status, 
           status_category, project, assignee, reporter, created, 
           updated, time_spent_seconds, url, 
           description_vector <=> '{embedding}' AS similarity
    FROM jira_task
    ORDER BY similarity DESC
    LIMIT 5
    """
    res.append(get_issues_from_db(sql))
    sql = f"""
    SELECT key, parent_key, summary, description, status, 
           status_category, assignee, created, 
           updated, time_spent_seconds, url, 
           description_vector <=> '{embedding}' AS similarity
    FROM jira_subtask
    ORDER BY similarity DESC
    LIMIT 5
    """
    res.append(get_issues_from_db(sql))

    sql = f"""
    SELECT key, parent_key, summary, description, issue_type, status,
              status_category, project, assignee, reporter, created, 
              updated, time_spent_seconds, url, 
              description_vector <=> '{embedding}' AS similarity
    FROM jira_bug
    ORDER BY similarity DESC
    LIMIT 5
    """
    res.append(get_issues_from_db(sql))

    return res


def get_tasks_and_subtasks_by_summary_similarity(text: str):
    """
    Retrieves the top 5 tasks and subtasks with the most similar summaries (vector-based match),
    but returns all metadata fields excluding vectors.

    Args:
        text (str): Input text to compare against summary vectors.

    Returns:
        list: Top 5 most similar tasks with the following fields: key, parent_key, summary,
              description, issue_type, status, status_category, project, assignee, 
              reporter, created, updated, time_spent_seconds, and url.
              """
    sql = f"""
    SELECT key, parent_key, summary, description, issue_type, status, 
           status_category, project, assignee, reporter, created, 
           updated, time_spent_seconds, url 
    FROM (
        SELECT * FROM jira_task
        UNION ALL
        SELECT * FROM jira_subtask
    ) AS combined_tasks
    ORDER BY summary_vector <=> '{text}'
    LIMIT 5
    """
    return get_issues_from_db(sql)


# --- Generic execution helper ---

def get_issues_from_db(sql_statement: str) -> list:
    """
    Fetches issues from the database and returns them as a list of dictionaries.
    """
    ALLOWED_TABLES = {"jira_task", "jira_subtask", "jira_bug"}

    if not any(f"FROM {table}" in sql_statement for table in ALLOWED_TABLES):
        logger.error(
            "Invalid SQL statement. " + 
            "Only 'jira_task', 'jira_subtask', and 'jira_bug' tables are allowed."
            )
        return ["Invalid SQL statement."]

    res = db_client.execute_sql(sql_statement)
    if res is None:
        logger.error("Query returned no results or failed.")
        return []
    logger.info("Query returned %d records.", len(res))
    return res

# --- LangGraph Agent Setup ---

service_agent = create_react_agent(
    model=model,
    tools=[
        get_tasks_by_assignee,
        get_tasks_by_project,
        get_bugs_by_status,
        get_subtasks_by_parent_key,
        get_tasks_by_description_similarity,
        get_tasks_and_subtasks_by_summary_similarity
    ],
    name="jira_query_agent",
    prompt="""You are a JIRA expert.
    You can help users query the JIRA database using tools that accept single parameters like assignee, project, or status.
    Use the tools to answer the user's question with relevant data."""
)

workflow = create_supervisor(
    [service_agent],
    model=model,
    prompt=(
        "You are a JIRA expert. You can help the user by using the following tools:\n"
        "- get_tasks_by_assignee(assignee: str)\n"
        "- get_tasks_by_project(project: str)\n"
        "- get_bugs_by_status(status: str)\n"
        "- get_subtasks_by_parent_key(parent_key: str)\n"
        "- get_tasks_by_text_similarity(text: str)\n"
        "All tools query one of the following tables: jira_task, jira_subtask, or jira_bug.\n"
        "Use them to retrieve information like key, status_category, and assignee."
    ),
    output_mode="full_history"
)

app = workflow.compile(
    checkpointer=checkpointer,
    store=store
)

config = {"configurable": {"thread_id": "thread-1"}}

def main():
    """
    Main function to run the agent and process user input.
    """
    if len(sys.argv) > 1:
        query = sys.argv[1]
    else:
        query = "Which tasks are related to expoloring the Agent Use Cases"

    result = app.invoke({
        "messages": [
            {
                "role": "user",
                "content": query
            }
        ]
    }, config=config)

    for m in result["messages"]:
        m.pretty_print()

if __name__ == "__main__":
    main()
