from typing import Optional, List, Union
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from textwrap import indent


class JiraUser(BaseModel):
    displayName: str
    emailAddress: str


class JiraWorklog(BaseModel):
    started: datetime
    timeSpent: str
    timeSpentSeconds: int


class JiraBaseIssue(BaseModel):
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
        return self.to_string()

    def to_string(self, detailed: bool = False) -> str:
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
    parent_key: str
    parent_summary: str

    def to_string(self, detailed: bool = False) -> str:
        base = super().to_string(detailed)
        if detailed:
            parent = f"Parent:      [{self.parent_key}] {self.parent_summary}"
            return base + "\n" + indent(parent, prefix="  ")
        return base


class JiraStory(JiraBaseIssue):
    subtasks: List[JiraSubtask] = Field(default_factory=list)

    def to_string(self, detailed: bool = False) -> str:
        base = super().to_string(detailed)
        if detailed and self.subtasks:
            subs = "\n".join(f"  - {s.to_string(detailed=False)}" for s in self.subtasks)
            return base + "\n  Subtasks:\n" + indent(subs, "    ")
        return base
