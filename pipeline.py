"""
This module contains functions to create and drop tables in the database.
It uses the `VectorDB` class to execute SQL commands for creating and dropping
tables related to Jira issues and subtasks.
It also includes logging to track the success or failure of these operations.
"""

import os
from dataclasses import dataclass
from typing import List

import dotenv
from jira import JIRA

from model.jira_models import JiraStory, JiraSubtask, JiraBug, JiraTask, JiraEpic
from jira_tools.factory import JiraFactory
from jira_tools.ingestor import JiraIngestor
from db.vectordb_client import VectorDB, DBConfig
from lib.logger import logger

# ------------------------------------------------------------------------------
# Configuration & Logging
# ------------------------------------------------------------------------------


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

        missing = [
            name
            for name, val in {
                "EMAIL": jira_email,
                "JIRA_AT": jira_token,
                "PG_PWD": pg_password,
            }.items()
            if not val
        ]

        if missing:
            raise EnvironmentError(
                f"The following environment variables are not set: {', '.join(missing)}"
            )

        return Config(
            jira_url="https://me-easy.atlassian.net",
            jira_email=jira_email,
            jira_token=jira_token,
            pg_password=pg_password,
        )


# ------------------------------------------------------------------------------
# Main Execution
# ------------------------------------------------------------------------------


def main():
    """
    Main function to fetch Jira issues, process them, and ingest them into the database.
    """
    # Load configuration and initialize clients
    config = Config.load_from_env()
    jira_client = JIRA(
        server=config.jira_url, basic_auth=(config.jira_email, config.jira_token)
    )

    # Get Projects
    projects = jira_client.projects() 
    for project in projects: 
        print(f"{project.key}: {project.name}")

    # Fetch and parse issues
    issues = fetch_issues(jira_client, jql="project=DATA")
    parsed_issues = [JiraFactory.create_issue(issue) for issue in issues]
    logger.info("Parsed %d issues", len(parsed_issues))

    # Separate stories and subtasks
    issue_types = {
        JiraStory: "stories",
        JiraSubtask: "subtasks",
        JiraTask: "tasks",
        JiraBug: "bugs",
        JiraEpic: "epics",
    }
    categorized_issues = {name: [] for name in issue_types.values()}

    for issue in parsed_issues:
        for issue_type, category in issue_types.items():
            if isinstance(issue, issue_type):
                categorized_issues[category].append(issue)
                break

    stories = categorized_issues["stories"]
    subtasks = categorized_issues["subtasks"]
    tasks = categorized_issues["tasks"]
    bugs = categorized_issues["bugs"]
    epics = categorized_issues["epics"]

    logger.info(
        "Epics %d, Stories: %d, Tasks %d, Subtasks: %d, Bugs: %d, Total: %d",
        len(epics),
        len(stories),
        len(tasks),
        len(subtasks),
        len(bugs),
        len(epics) + len(stories) + len(tasks) + len(subtasks) + len(bugs),
    )

    issue_data76 = [
        issue for issue in parsed_issues if issue.key == "DATA-76"
    ][0]

    from jira_tools.attachement_handler import AttachementHandler
    import json
    attachement_hdlr = AttachementHandler(jira_client)
    print(json.dumps(attachement_hdlr.process_attachements(
        issue_data76, save_file=True
    )))
    # for categorized_issues in parsed_issues:
    #     attachement_hdlr.process_attachements(
    #         categorized_issues, save_file=True
    #     )

    return

    # Initialize DB and ingest
    db_client = VectorDB(
        DBConfig(
            dbname=config.pg_dbname,
            user=config.pg_user,
            password=config.pg_password,
            host=config.pg_host,
        )
    )
    ingestor = JiraIngestor(db_client)
    ingestor.ingest_bulk(epics=epics, stories=stories, subtasks=subtasks, bugs=bugs, tasks=tasks)


# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------


def fetch_issues(jira_client: JIRA, jql: str) -> List:
    """
    Fetch issues from Jira using the provided JQL query.
    """
    issues = []
    start_at = 0
    max_results = 100

    while batch := jira_client.search_issues(
        jql, startAt=start_at, maxResults=max_results
    ):
        issues.extend(batch)
        start_at += max_results
        if len(batch) < max_results:
            break

    logger.info("Number of issues found: %d", len(issues))
    return issues


def print_issues(title: str, issues: List):
    """
    Print a list of issues with a given title.
    """
    print(f"\n{title}:")
    for issue in issues:
        print(issue.to_string(detailed=True))


# ------------------------------------------------------------------------------
# Entry Point
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
