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
    JiraEpic,
    JiraAttachement,
    Author
)
from lib.logger import logger
from jira.resources import Issue 

class JiraFactory:
    """
    A factory class for creating and parsing Jira-related objects.
    This class provides static methods to parse Jira user data, worklogs,
    and create Jira issue objects such as subtasks and stories.
    """
    @staticmethod
    def get_field(issue_fields, field_name, is_dict, default=None):
        value = issue_fields.get(field_name, default) if is_dict else getattr(issue_fields, field_name, default) if hasattr(issue_fields, field_name) else default
        return value if value not in (None, "") else default

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
            is_dict = isinstance(user, dict)
            return JiraUser(
                displayName=JiraFactory.get_field(user, "displayName", is_dict=is_dict),
                emailAddress=JiraFactory.get_field(user, "emailAddress", default="No person assigned.", is_dict=is_dict),
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
    def parse_author(author_obj) -> Optional[JiraUser]:
        """
        Parse a Jira author object into a JiraUser instance.
        Args:
            author_obj: The Jira author object to parse.
        Returns:
            Optional[JiraUser]: A JiraUser instance if the author object is valid,
            otherwise None.
        Raises:
            ValueError: If the author object is invalid or missing required attributes.
        """
        if author_obj:
            is_dict = isinstance(author_obj, dict)
            return Author(
                accountId=JiraFactory.get_field(author_obj, "accountId", is_dict=is_dict),
                displayName=JiraFactory.get_field(author_obj, "displayName", is_dict=is_dict),
            )
        return None

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

        def parse_fields(issue_fields, is_dict=False):

            return {
            "key": issue['key'] if is_dict else issue.key,
            "summary": JiraFactory.get_field(
                issue_fields, "summary", is_dict
            ),
            "description": JiraFactory.get_field(
                issue_fields, "description", is_dict, "No description"
            ),
            "status": (
                JiraFactory.get_field(issue_fields, "status", is_dict)["name"]
                if is_dict
                else JiraFactory.get_field(issue_fields, "status", is_dict).name
            ),
            "statusCategory": (
                JiraFactory.get_field(issue_fields, "status", is_dict)["statusCategory"]["name"]
                if is_dict
                else JiraFactory.get_field(issue_fields, "status", is_dict).statusCategory.name
            ),
            "project": (
                JiraFactory.get_field(issue_fields, "project", is_dict)["name"]
                if is_dict
                else JiraFactory.get_field(issue_fields, "project", is_dict).name
            ),
            "issue_type": (
                JiraFactory.get_field(issue_fields, "issuetype", is_dict)["name"]
                if is_dict
                else JiraFactory.get_field(issue_fields, "issuetype", is_dict).name
            ),
            "assignee": JiraFactory.parse_user(
                JiraFactory.get_field(issue_fields, "assignee", is_dict)
            ),
            "reporter": JiraFactory.parse_user(
                JiraFactory.get_field(issue_fields, "reporter", is_dict)
            ),
            "created": JiraFactory.get_field(issue_fields, "created", is_dict),
            "updated": JiraFactory.get_field(issue_fields, "updated", is_dict),
            "timeSpentSeconds": JiraFactory.get_field(
                issue_fields, "timespent", is_dict, 0
            ),
            "url": issue["self"] if is_dict else issue.self,
            "worklogs": JiraFactory.parse_worklogs(
                JiraFactory.get_field(issue_fields, "worklog", is_dict, {})
            ),
            "attachments": [
                JiraAttachement(
                    id=att["id"] if is_dict else att.id,
                    filename=att["filename"] if is_dict else att.filename,
                    author=JiraFactory.parse_author(
                        att.get("author") if is_dict else att.author
                    ),
                    created=att["created"] if is_dict else att.created,
                    size=att["size"] if is_dict else att.size,
                    mimeType=att["mimeType"] if is_dict else att.mimeType,
                    content=att["content"] if is_dict else att.content,
                )
                for att in JiraFactory.get_field(issue_fields, "attachment", is_dict, [])
                if isinstance(
                    JiraFactory.get_field(issue_fields, "attachment", is_dict, []), list
                )
            ]
            if JiraFactory.get_field(issue_fields, "attachment", is_dict)
            else [],
            }

        if isinstance(issue, Issue):
            fields = issue.fields
            base_kwargs = parse_fields(fields)
        else:
            fields = issue['fields']
            base_kwargs = parse_fields(fields, is_dict=True)

        if '981' in issue.key:
            pass

        if fields["issuetype"]["subtask"] if isinstance(fields, dict) else fields.issuetype.subtask:
            return JiraSubtask(
            **base_kwargs,
            parent_key=fields["parent"]["key"] if isinstance(fields, dict) else fields.parent.key,
            parent_summary=fields["parent"]["fields"]["summary"] if isinstance(fields, dict) else fields.parent.fields.summary,
            )
        elif (fields["issuetype"]["name"] if isinstance(fields, dict) else fields.issuetype.name) == "Epic":
            return JiraEpic(**base_kwargs)
        elif (fields["issuetype"]["name"] if isinstance(fields, dict) else fields.issuetype.name) in ("Story", "Innovation"):
            return JiraStory(**base_kwargs)
        elif (fields["issuetype"]["name"] if isinstance(fields, dict) else fields.issuetype.name) == "Task":
            if ("parent" in fields and fields["parent"]) if isinstance(fields, dict) else (hasattr(fields, "parent") and fields.parent):
                return JiraTask(
                    **base_kwargs,
                    parent_key=fields["parent"]["key"] if isinstance(fields, dict) else fields.parent.key,
                    parent_summary=fields["parent"]["fields"]["summary"] if isinstance(fields, dict) else fields.parent.fields.summary,
                )
            return JiraTask(**base_kwargs)
        elif (fields["issuetype"]["name"] if isinstance(fields, dict) else fields.issuetype.name) == "Bug":
            return JiraBug(
            **base_kwargs,
            fixed=fields["fixVersions"] if isinstance(fields, dict) else fields.fixVersions,
            )

        logger.warning(
            "Unhandled type of %s is: %s of Element: %s",
            issue.key,
            fields.issuetype.name,
            fields.summary,
        )
        return JiraBaseIssue(**base_kwargs)
