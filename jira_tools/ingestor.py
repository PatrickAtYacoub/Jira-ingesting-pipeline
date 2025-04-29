"""
This module contains functions to create and drop tables in the database.
It uses the `VectorDB` class to execute SQL commands for creating and dropping tables
related to Jira issues and subtasks.
It also includes logging to track the success or failure of these operations.
"""

from typing import List
from db.vectordb_client import VectorDB
from model.jira_models import JiraStory, JiraSubtask, JiraBug, JiraTask, JiraBaseIssue, JiraEpic
from logger import logger
from psycopg2 import DatabaseError


class JiraIngestor:
    """
    A class responsible for ingesting Jira issues and subtasks into a vector database.
    """

    def __init__(self, client: VectorDB):
        """
        Initialize the JiraIngestor with a VectorDB client.

        Args:
            client (VectorDB): The vector database client used for storing Jira data.
        """
        self.client = client

    def ingest_issue(self, issue):
        """
        Inserts the issue into the appropriate table depending on its type.
        Supports JiraIssue, JiraTask, JiraBug, JiraSubtask, JiraEpic, etc.
        """

        def sql_escape(value):
            return str(value).replace("'", "''") if value else ""

        try:
            summary_embedding = self.client.create_embedding(issue.summary)
            description_embedding = self.client.create_embedding(issue.description)

            if isinstance(issue, JiraSubtask):
                self.client.execute_sql("insert_jira_subtask",
                    key=issue.key,
                    parent_key=issue.parent_key,
                    summary=sql_escape(issue.summary),
                    summary_vector=summary_embedding,
                    status=issue.status,
                    status_category=issue.statusCategory,
                    assignee=issue.assignee.displayName if issue.assignee else "",
                    created=issue.created,
                    updated=issue.updated,
                    time_spent_seconds=issue.timeSpentSeconds or 0,
                    url=str(issue.url)
                )

            elif isinstance(issue, JiraTask) or isinstance(issue, JiraEpic) or isinstance(issue, JiraStory):
                self.client.execute_sql("insert_jira_task",
                    key=issue.key,
                    summary=sql_escape(issue.summary),
                    summary_vector=summary_embedding,
                    description=sql_escape(issue.description),
                    description_vector=description_embedding,
                    issue_type=issue.issue_type,
                    status=issue.status,
                    status_category=issue.statusCategory,
                    parent_key=issue.parent_key if hasattr(issue, 'parent_key') else None,
                    project=issue.project,
                    assignee=issue.assignee.displayName if issue.assignee else "",
                    reporter=issue.reporter.displayName if issue.reporter else "",
                    created=issue.created,
                    updated=issue.updated,
                    time_spent_seconds=issue.timeSpentSeconds or 0,
                    url=str(issue.url)
                )

            elif isinstance(issue, JiraBug):
                self.client.execute_sql("insert_jira_bug",
                    key=issue.key,
                    summary=sql_escape(issue.summary),
                    summary_vector=summary_embedding,
                    description=sql_escape(issue.description),
                    description_vector=description_embedding,
                    issue_type=issue.issue_type,
                    status=issue.status,
                    status_category=issue.statusCategory,
                    project=issue.project,
                    assignee=issue.assignee.displayName if issue.assignee else "",
                    reporter=issue.reporter.displayName if issue.reporter else "",
                    created=issue.created,
                    updated=issue.updated,
                    time_spent_seconds=issue.timeSpentSeconds or 0,
                    url=str(issue.url)
                )

            else:
                raise ValueError(f"Unsupported issue type: {type(issue).__name__}")

            logger.info("Ingested %s: %s", type(issue).__name__, issue.key)

        except (AttributeError, KeyError, ValueError, TypeError, RuntimeError) as e:
            logger.error("Error while ingesting %s %s: %s", issue.__class__.__name__, issue.key, e)
        except DatabaseError as db_err:
            logger.error("Database error while ingesting %s %s: %s", 
                         issue.__class__.__name__, issue.key, db_err)


    def ingest_subtask(self, subtask: JiraSubtask):
        """
        Ingest a Jira subtask into the vector database.

        Args:
            subtask (JiraSubtask): The Jira subtask to be ingested.

        Logs:
            Logs success or failure of the ingestion process.
        """
        try:
            summary_embedding = self.client.create_embedding(subtask.summary)

            self.client.execute_sql("insert_jira_subtask",
                key=subtask.key,
                parent_key=subtask.parent_key,
                summary=subtask.summary.replace("'", "''"),
                summary_vector=summary_embedding,
                status=subtask.status,
                status_category=subtask.statusCategory,
                assignee=subtask.assignee.displayName if subtask.assignee else "",
                created=subtask.created,
                updated=subtask.updated,
                time_spent_seconds=subtask.timeSpentSeconds or 0,
                url=str(subtask.url)
            )
            logger.info("Ingested Jira Subtask: %s", subtask.key)
        except AttributeError as e:
            logger.error("Attribute error while ingesting Jira Subtask %s: %s", subtask.key, e)
        except KeyError as e:
            logger.error("Key error while ingesting Jira Subtask %s: %s", subtask.key, e)
        except ValueError as e:
            logger.error("Value error while ingesting Jira Subtask %s: %s", subtask.key, e)
        except (TypeError, RuntimeError) as e:
            logger.error("Unexpected error ingesting Jira Subtask %s: %s", subtask.key, e)


    def ingest_bulk(
        self,
        epics: List[JiraBaseIssue],
        stories: List[JiraStory],
        subtasks: List[JiraSubtask],
        bugs: List[JiraBug],
        tasks: List[JiraTask]
    ):
        """
        Ingest multiple Jira issues and subtasks into the vector database in correct dependency order.

        Order:
            1. Epics
            2. Stories, Tasks, Bugs (linked to Epics or independent)
            3. Subtasks (require parent issue to exist)

        Args:
            epics (List[JiraBaseIssue]): A list of Jira epics.
            stories (List[JiraStory]): A list of Jira stories.
            subtasks (List[JiraSubtask]): A list of Jira subtasks.
            bugs (List[JiraBug]): A list of Jira bugs.
            tasks (List[JiraTask]): A list of Jira tasks.

        Logs:
            Logs success or failure of the ingestion process for each issue and subtask.
        """

        # 1. Epics
        for epic in epics:
            try:
                self.ingest_issue(epic)
            except (ValueError, DatabaseError) as e:
                logger.error("Failed to ingest epic %s: %s", epic.key, e)

        # 2. Stories, Tasks, Bugs
        for issue in stories + tasks + bugs:
            try:
                self.ingest_issue(issue)
            except (ValueError, DatabaseError) as e:
                logger.error("Failed to ingest issue %s: %s", issue.key, e)

        # 3. Subtasks
        for subtask in subtasks:
            try:
                parent_issue_exists = self.client.execute_sql(
                    "issue_exists",
                    key=subtask.parent_key
                )
                if parent_issue_exists[0][0]:
                    self.ingest_subtask(subtask)
                else:
                    logger.warning("Parent issue %s not found for subtask %s",
                                subtask.parent_key, subtask.key)
            except (KeyError, DatabaseError) as e:
                logger.error("Failed to ingest subtask %s: %s", subtask.key, e)