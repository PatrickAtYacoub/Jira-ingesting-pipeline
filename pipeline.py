"""
This module contains functions to create and drop tables in the database.
It uses the `VectorDB` class to execute SQL commands for creating and dropping tables related to Jira issues and subtasks.
It also includes logging to track the success or failure of these operations.
"""

import os
import logging
from dataclasses import dataclass
from typing import List

import dotenv
from jira import JIRA

from model.jira_models import JiraStory, JiraSubtask
from jira_tools.factory import JiraFactory
from jira_tools.ingestor import JiraIngestor
from db.vectordb_client import VectorDB, DBConfig

# ------------------------------------------------------------------------------
# Configuration & Logging
# ------------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Config:
    jira_url: str
    jira_email: str
    jira_token: str
    pg_password: str
    pg_dbname: str = "hackathon_ofa"
    pg_user: str = "hackathon_ofa"
    pg_host: str = "hackathon-ofa.postgres.database.azure.com"

    @staticmethod
    def load_from_env() -> "Config":
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


# ------------------------------------------------------------------------------
# Main Execution
# ------------------------------------------------------------------------------

def main():
    # Load configuration and initialize clients
    config = Config.load_from_env()
    jira_client = JIRA(server=config.jira_url, basic_auth=(config.jira_email, config.jira_token))

    # Fetch and parse issues
    issues = fetch_issues(jira_client, jql="project=DATA AND assignee=currentUser()")
    parsed_issues = [JiraFactory.create_issue(issue) for issue in issues]

    # Separate stories and subtasks
    stories = [issue for issue in parsed_issues if isinstance(issue, JiraStory)]
    subtasks = [issue for issue in parsed_issues if isinstance(issue, JiraSubtask)]

    logger.info(f"Stories: {len(stories)}, Subtasks: {len(subtasks)}")

    print_issues("Stories", stories)
    print_issues("Subtasks", subtasks)

    # Initialize DB and ingest
    db_client = VectorDB(
        DBConfig(
            dbname=config.pg_dbname,
            user=config.pg_user,
            password=config.pg_password,
            host=config.pg_host
        )
    )
    ingestor = JiraIngestor(db_client)
    ingestor.ingest_bulk(issues=stories, subtasks=subtasks)


# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------

def fetch_issues(jira_client: JIRA, jql: str) -> List:
    issues = jira_client.search_issues(jql)
    logger.info(f"Number of issues found: {len(issues)}")
    return issues


def print_issues(title: str, issues: List):
    print(f"\n{title}:")
    for issue in issues:
        print(issue.to_string(detailed=True))


# ------------------------------------------------------------------------------
# Entry Point
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
