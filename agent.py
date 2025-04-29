"""
This module contains functions to create and drop tables in the database.
It uses the `VectorDB` class to execute SQL commands for creating and dropping tables related to Jira issues and subtasks.
It also includes logging to track the success or failure of these operations.
"""

import sys
import os
from dataclasses import dataclass
import dotenv
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from langchain_openai import AzureChatOpenAI
from db.vectordb_client import VectorDB, DBConfig
from logger import agent_logger as logger

checkpointer = InMemorySaver()
store = InMemoryStore()

@dataclass(frozen=True)
class Config:
    """
    Configuration class to hold environment variables and database credentials.
    """
    jira_url: str
    jira_email: str
    jira_token: str
    pg_password: str
    pg_dbname: str = "hackathon_ofa"
    pg_user: str = "hackathon_ofa"
    pg_host: str = "hackathon-ofa.postgres.database.azure.com"
    azure_chat_openai_api_version: str = "2024-02-01"
    azure_chat_openai_base_url: str = "https://oai-hackathon-ofa.openai.azure.com/"
    azure_chat_openai_instanceName = "oai-hackathon-ofa"

    @staticmethod
    def load_from_env() -> "Config":
        """
        Load configuration from environment variables.
        Raises an error if required variables are missing.
        """
        dotenv.load_dotenv()

        jira_email = os.getenv("EMAIL")
        jira_token = os.getenv("JIRA_AT")
        pg_password = os.getenv("PG_PWD")

        missing = [name for name, val in {
            "EMAIL": jira_email,
            "JIRA_AT": jira_token,
            "PG_PWD": pg_password
        }.items() if not val]

        if missing:
            raise EnvironmentError(
                f"The following environment variables are not set: {', '.join(missing)}"
            )

        return Config(
            jira_url="https://me-easy.atlassian.net",
            jira_email=jira_email,
            jira_token=jira_token,
            pg_password=pg_password
        )

config = Config.load_from_env()

model = AzureChatOpenAI(
    azure_deployment="gpt-4o-mini",
    azure_endpoint=config.azure_chat_openai_base_url,
    azure_api_version=config.azure_chat_openai_api_version,
    model_name="gpt-4o-mini", )

db_client = VectorDB(
        DBConfig(
            dbname=config.pg_dbname,
            user=config.pg_user,
            password=config.pg_password,
            host=config.pg_host
        )
    )


def get_issues_from_db():
    """
    Fetches issues from the database and returns them as a list of dictionaries.
    """
    res = db_client.execute_sql(
        """
        SELECT key, status_category, assignee FROM jira_issue;
        """
    )
    if res is None:
        logger.error("Table does not exist.")
        return []
    else:
        logger.info("Found %d records in the 'jira_issue' table.", len(res))
        return [{"key": key[0], "status_category": key[1], "assignee": key[2]} for key in res]


service_agent = create_react_agent(
    model=model,
    tools=[get_issues_from_db],
    name="service_expert",
    prompt="""You are a JIRA expert.
    You can also help users with your tools."""
)

# Create supervisor workflow
workflow = create_supervisor(
    [service_agent],
    model=model,
    prompt=(
        "You are a JIRA expert. "
        "You can ask the user for more information if needed."
        "You have access to the following tools: "
        "- get_issues_from_db: Get issues from the database. "
    ),
    output_mode="full_history"
)

# Compile and run
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
        # Get the user input
        query = sys.argv[1]
    else:
        # Default query
        query = "Which tasks are currently assigned to Patrick Scheich"

    result = app.invoke({
    "messages": [
        {
            "role": "user",
            # "content": "With which IT Systems do we have most problems?"
            "content": query
        }
    ]
}, config=config)

    for m in result["messages"]:
        m.pretty_print()

if __name__ == "__main__":
    main()
