"""
This module contains functions to create and drop tables in the database.
It uses the `VectorDB` class to execute SQL commands for creating and dropping
tables related to Jira issues and subtasks.
It also includes logging to track the success or failure of these operations.
"""

from typing import Optional, List, Union
from model.jira_models import (
    JiraUser,
    JiraWorklog,
    JiraSubtask,
    JiraStory,
    JiraTask,
    JiraBaseIssue,
    JiraBug,
    JiraEpic
)
from logger import logger

class JiraFactory:
    """
    A factory class for creating and parsing Jira-related objects.
    This class provides static methods to parse Jira user data, worklogs,
    and create Jira issue objects such as subtasks and stories.
    """

    @staticmethod
    def parse_user(user) -> Optional[JiraUser]:
        """
        Parse a Jira user object into a JiraUser instance.
        Args:
            user: The Jira user object to parse.
        Returns:
            Optional[JiraUser]: A JiraUser instance if the user object is valid,
            otherwise None.
        Raises:
            ValueError: If the user object is invalid or missing required attributes.
        """
        if user:
            return JiraUser(
                displayName=user.displayName,
                emailAddress=getattr(user, "emailAddress", "No Person assigned."),
            )
        return None

    @staticmethod
    def parse_worklogs(worklog_obj) -> List[JiraWorklog]:
        """
        Parse a Jira worklog object into a list of JiraWorklog instances.
        Args:
            worklog_obj: The Jira worklog object to parse.
        Returns:
            List[JiraWorklog]: A list of JiraWorklog instances if the worklog
            object contains worklogs, otherwise an empty list.

        Raises:
            ValueError: If the worklog object is invalid or missing required attributes.
        """
        return (
            [
                JiraWorklog(
                    started=w.started,
                    timeSpent=w.timeSpent,
                    timeSpentSeconds=w.timeSpentSeconds,
                )
                for w in worklog_obj.worklogs
            ]
            if hasattr(worklog_obj, "worklogs")
            else []
        )

    @staticmethod
    def create_issue(issue) -> Union[JiraSubtask, JiraStory]:
        """
        Create a Jira issue object (subtask or story) from a Jira issue.
        Args:
            issue: The Jira issue object to create from.
        Returns:
            Union[JiraSubtask, JiraStory]: A JiraSubtask instance if the issue
            is a subtask, otherwise a JiraStory instance.

        Raises:

        """
        fields = issue.fields
        base_kwargs = {
            "key": issue.key,
            "summary": fields.summary,
            "description": (
                fields.description if fields.description else "No description"
            ),
            "status": fields.status.name,
            "statusCategory": fields.status.statusCategory.name,
            "project": fields.project.name,
            "issue_type": fields.issuetype.name,
            "assignee": JiraFactory.parse_user(fields.assignee),
            "reporter": JiraFactory.parse_user(fields.reporter),
            "created": fields.created,
            "updated": fields.updated,
            "timeSpentSeconds": fields.timespent,
            "url": issue.self,
            "worklogs": JiraFactory.parse_worklogs(fields.worklog),
        }

        if fields.issuetype.subtask:
            return JiraSubtask(
                **base_kwargs,
                parent_key=fields.parent.key,
                parent_summary=fields.parent.fields.summary,
            )
        elif fields.issuetype.name == "Epic":
            return JiraEpic(**base_kwargs)
        elif fields.issuetype.name in ("Story", "Innovation"):
            return JiraStory(**base_kwargs)
        elif fields.issuetype.name == "Task":
            if hasattr(fields, "parent") and fields.parent:
                return JiraTask(
                    **base_kwargs,
                    parent_key=fields.parent.key,
                    parent_summary=fields.parent.fields.summary,
                )
            return JiraTask(**base_kwargs)
        elif fields.issuetype.name == "Bug":
            return JiraBug(**base_kwargs, fixed=fields.fixVersions)

        logger.warning(
            "Unhandled type of %s is: %s of Element: %s",
            issue.key,
            fields.issuetype.name,
            fields.summary,
        )
        return JiraBaseIssue(**base_kwargs)
