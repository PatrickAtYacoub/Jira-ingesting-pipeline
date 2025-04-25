"""
This module defines Pydantic models for representing Jira entities such as users, worklogs, issues, subtasks, and stories.
These models provide a structured way to handle Jira data and include methods for generating string representations.
"""

from typing import Optional, List
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from textwrap import indent


class JiraUser(BaseModel):
    """
    Represents a Jira user.

    Attributes:
        displayName (str): The display name of the user.
        emailAddress (str): The email address of the user.
    """
    displayName: str
    emailAddress: str

    def __str__(self) -> str:
        return f"{self.displayName} <{self.emailAddress}>"
    
    def to_string(self) -> str:
        """
        Returns a string representation of the user.
        """
        return self.__str__()


class JiraWorklog(BaseModel):
    """
    Represents a Jira worklog entry.

    Attributes:
        started (datetime): The start time of the worklog.
        timeSpent (str): The time spent on the worklog in human-readable format.
        timeSpentSeconds (int): The time spent on the worklog in seconds.
    """
    started: datetime
    timeSpent: str
    timeSpentSeconds: int

    def __str__(self) -> str:
        return f"{self.timeSpent} ({self.timeSpentSeconds} seconds)"
    
    def to_string(self) -> str:
        """
        Returns a string representation of the worklog.
        """
        return self.__str__()


class JiraBaseIssue(BaseModel):
    """
    Represents a base Jira issue.

    Attributes:
        key (str): The unique key of the issue.
        summary (str): A brief summary of the issue.
        description (str): A detailed description of the issue.
        status (str): The current status of the issue.
        statusCategory (str): The category of the issue's status.
        project (str): The project to which the issue belongs.
        issue_type (str): The type of the issue (e.g., Bug, Task).
        assignee (Optional[JiraUser]): The user assigned to the issue.
        reporter (Optional[JiraUser]): The user who reported the issue.
        created (datetime): The creation timestamp of the issue.
        updated (datetime): The last updated timestamp of the issue.
        timeSpentSeconds (Optional[int]): The total time spent on the issue in seconds.
        url (HttpUrl): The URL to the issue in Jira.
        worklogs (List[JiraWorklog]): A list of worklogs associated with the issue.
    """
    key: str
    summary: str
    description: str
    status: str
    statusCategory: str
    project: str
    issue_type: str
    assignee: Optional[JiraUser]
    reporter: Optional[JiraUser]
    created: datetime
    updated: datetime
    timeSpentSeconds: Optional[int]
    url: HttpUrl
    worklogs: List[JiraWorklog] = Field(default_factory=list)

    def __str__(self) -> str:
        """
        Returns a string representation of the issue.
        """
        return self.to_string()

    def to_string(self, detailed: bool = False) -> str:
        """
        Generates a string representation of the issue.

        Args:
            detailed (bool): Whether to include detailed information.

        Returns:
            str: The string representation of the issue.
        """
        base = f"[{self.key}] {self.summary} ({self.status})"
        if not detailed:
            return base
        details = [
            f"Description: {self.description}",
            f"Type:        {self.issue_type}",
            f"Project:     {self.project}",
            f"Status Cat.: {self.statusCategory}",
            f"Assignee:    {self.assignee.displayName if self.assignee else '-'}",
            f"Reporter:    {self.reporter.displayName if self.reporter else '-'}",
            f"Created:     {self.created}",
            f"Updated:     {self.updated}",
            f"Time Spent:  {self.timeSpentSeconds // 3600 if self.timeSpentSeconds else 0}h",
            f"Link:        {self.url}"
        ]
        return base + "\n" + indent("\n".join(details), prefix="  ")


class JiraSubtask(JiraBaseIssue):
    """
    Represents a Jira subtask, which is a specialized type of issue.

    Attributes:
        parent_key (str): The key of the parent issue.
        parent_summary (str): The summary of the parent issue.
    """
    parent_key: str
    parent_summary: str

    def to_string(self, detailed: bool = False) -> str:
        """
        Generates a string representation of the subtask.

        Args:
            detailed (bool): Whether to include detailed information.

        Returns:
            str: The string representation of the subtask.
        """
        base = super().to_string(detailed)
        if detailed:
            parent = f"Parent:      [{self.parent_key}] {self.parent_summary}"
            return base + "\n" + indent(parent, prefix="  ")
        return base


class JiraStory(JiraBaseIssue):
    """
    Represents a Jira story, which may contain subtasks.

    Attributes:
        subtasks (List[JiraSubtask]): A list of subtasks associated with the story.
    """
    subtasks: List[JiraSubtask] = Field(default_factory=list)

    def to_string(self, detailed: bool = False) -> str:
        """
        Generates a string representation of the story.

        Args:
            detailed (bool): Whether to include detailed information.

        Returns:
            str: The string representation of the story.
        """
        base = super().to_string(detailed)
        if detailed and self.subtasks:
            subs = "\n".join(f"  - {s.to_string(detailed=False)}" for s in self.subtasks)
            return base + "\n  Subtasks:\n" + indent(subs, "    ")
        return base
