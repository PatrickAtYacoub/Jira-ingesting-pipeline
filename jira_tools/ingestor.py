"""
This module contains functions to create and drop tables in the database.
It uses the `VectorDB` class to execute SQL commands for creating and dropping tables
related to Jira issues and subtasks.
It also includes logging to track the success or failure of these operations.
"""

import logging
from typing import List
from db.vectordb_client import VectorDB
from model.jira_models import JiraStory, JiraSubtask


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

    def ingest_issue(self, issue: JiraStory):
        """
        Ingest a Jira issue (story) into the vector database.

        Args:
            issue (JiraStory): The Jira story to be ingested.

        Logs:
            Logs success or failure of the ingestion process.
        """
        try:
            summary_embedding = self.client.create_embedding(issue.summary)
            description_embedding = self.client.create_embedding(issue.description)

            self.client.execute_sql("insert_jira_issue",
                key=issue.key,
                summary=issue.summary.replace("'", "''"),
                summary_vector=summary_embedding,
                description=issue.description.replace("'", "''"),
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
            logging.info("Ingested Jira Issue: %s", issue.key)
        except AttributeError as e:
            logging.error("Attribute error while ingesting Jira Issue %s: %s", issue.key, e)
        except KeyError as e:
            logging.error("Key error while ingesting Jira Issue %s: %s", issue.key, e)
        except ValueError as e:
            logging.error("Value error while ingesting Jira Issue %s: %s", issue.key, e)
        except Exception as e:
            logging.error("Unexpected error ingesting Jira Issue %s: %s", issue.key, e)

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
            logging.info("Ingested Jira Subtask: %s", subtask.key)
        except AttributeError as e:
            logging.error("Attribute error while ingesting Jira Subtask %s: %s", subtask.key, e)
        except KeyError as e:
            logging.error("Key error while ingesting Jira Subtask %s: %s", subtask.key, e)
        except ValueError as e:
            logging.error("Value error while ingesting Jira Subtask %s: %s", subtask.key, e)
        except Exception as e:
            logging.error("Unexpected error ingesting Jira Subtask %s: %s", subtask.key, e)

    def ingest_bulk(self, issues: List[JiraStory], subtasks: List[JiraSubtask]):
        """
        Ingest multiple Jira issues and subtasks into the vector database.

        Args:
            issues (List[JiraStory]): A list of Jira stories to be ingested.
            subtasks (List[JiraSubtask]): A list of Jira subtasks to be ingested.

        Logs:
            Logs success or failure of the ingestion process for each issue and subtask.
        """
        # First, ingest all issues (stories)
        for issue in issues:
            self.ingest_issue(issue)

        # Then, ingest subtasks, ensuring that the parent issue exists
        for subtask in subtasks:
            # Check if the parent issue exists in the database
            parent_issue_exists = self.client.execute_sql(
                "issue_exists", 
                key=subtask.parent_key
            )
            if parent_issue_exists[0][0]:
                self.ingest_subtask(subtask)
            else:
                logging.warning("Parent issue %s not found for subtask %s",
                                subtask.parent_key, subtask.key
                                )
