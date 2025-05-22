"""
This module contains functions to create and drop tables in the database.
It uses the `VectorDB` class to execute SQL commands for creating and dropping
tables related to Jira issues and subtasks.
It also includes logging to track the success or failure of these operations.
"""

from typing import List
from jira_tools import JiraHandler, JiraIngestor, AttachementHandler
from db import VectorDB, DBConfig
from lib.logger import logger

# ------------------------------------------------------------------------------
# Main Execution
# ------------------------------------------------------------------------------
def main():
    """
    Main function to fetch Jira issues, process them, and ingest them into the database.
    """

    handler = JiraHandler()
    parsed_issues = handler.fetch_and_parse_issues(jql="project=DATA")
    categorized_issues = handler.categorize_issues(parsed_issues)
    jira_client = handler.get_client()

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

    import json
    issue_data167 = [
        issue for issue in parsed_issues if issue.key == "DATA-167"
    ][0]

    return
    attachement_hdlr = AttachementHandler(jira_client)
    print(json.dumps(attachement_hdlr.process_attachements(
        issue_data167, save_file=True
    )))
    # for categorized_issues in parsed_issues:
    #     attachement_hdlr.process_attachements(
    #         categorized_issues, save_file=True
    #     )


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
