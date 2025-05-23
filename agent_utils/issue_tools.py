"""
Module: issue_tools
-------------------
This module provides utility functions for interacting with Jira issues,
including fetching complete issue details and converting them to Pydantic models.
Fetches the complete details of a Jira issue and returns it as a Pydantic model.
This function retrieves all available fields for the specified Jira issue by making
an authenticated HTTP GET request to the Jira API. The response is then validated
and parsed into a `JiraIssueResponse` Pydantic model.
    issue (JiraBaseIssue): The Jira issue object containing at least the issue URL.
    JiraIssueResponse: A Pydantic model containing all fields of the Jira issue.
Raises:
    Exception: If the HTTP request to fetch the issue details fails.
"""

from pydantic import BaseModel
import requests
from config import Config
import base64
import collections
from typing import List, Dict, Optional, Set

from jira_tools import JiraHandler
from model.jira_models import JiraBaseIssue

class JiraIssueResponse(BaseModel):
    # Accept all fields dynamically
    class Config:
        extra = "allow"

def get_complete_issue(issue_keys) -> List[JiraIssueResponse]:
    """
    Returns the complete Issue Model(s) for one or more Jira issues from the Jira API.

    Args:
        issue_keys (Union[str, List[str]]): The key or list of keys of the Jira issues to fetch.

    Returns:
        List[JiraIssueResponse]: List of JSON Models of the complete issues.
    """
    if isinstance(issue_keys, str):
        issue_keys = [issue_keys]

    conf = Config.load_from_env()
    user = conf.jira_email
    token = conf.jira_token

    # Basic Auth header: base64("email:api_token")
    auth_str = f"{user}:{token}"
    b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")

    headers = {
        "Accept": "application/json",
        "Authorization": f"Basic {b64_auth}",
    }

    responses = []
    for issue_key in issue_keys:
        url = f"https://me-easy.atlassian.net/rest/api/2/issue/{issue_key}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            responses.append(JiraIssueResponse.model_validate(response.json()))
        else:
            raise Exception(f"Failed to fetch issue details for {issue_key}: {response.status_code} - {response.text}")
    return responses
    

class IssueNotFoundException(Exception):
    """Custom exception raised when an issue is not found."""
    pass

class IssueRepository:
    """
    Manages the storage and retrieval of Jira issues, providing efficient lookup.
    Adheres to the Single Responsibility Principle.
    """
    def __init__(self, issues: List[JiraBaseIssue]): # Now 'JiraBaseIssue' is correctly typed
        # Optimize issue lookup by creating a dictionary mapping issue keys to JiraBaseIssue objects.
        self._issue_map: Dict[str, JiraBaseIssue] = {issue.key: issue for issue in issues}

    def get_issue(self, issue_key: str) -> Optional[JiraBaseIssue]:
        """Retrieves an JiraBaseIssue object by its key."""
        return self._issue_map.get(issue_key)

    def get_all_issues(self) -> List[JiraBaseIssue]:
        """Returns all issues currently in the repository."""
        return list(self._issue_map.values())

class JiraIssueService:
    """
    Service layer responsible for interacting with Jira and providing issue-related business logic.
    Adheres to the Single Responsibility Principle and Dependency Inversion Principle.
    """
    def __init__(self, jira_handler: JiraHandler, issue_repository: IssueRepository):
        self._jira_handler = jira_handler
        self._issue_repository = issue_repository

    def get_issue_by_key(self, issue_key: str) -> JiraBaseIssue: # Return type changed to JiraBaseIssue
        """
        Fetches a single issue by its key from the repository.
        Raises IssueNotFoundException if the issue does not exist.
        """
        issue = self._issue_repository.get_issue(issue_key)
        if not issue:
            raise IssueNotFoundException(f"Issue with key '{issue_key}' not found.")
        return issue

    def get_connected_issues(self, issue_key: str) -> List[JiraBaseIssue]: # Return type changed to JiraBaseIssue
        """
        Returns a list of all directly and indirectly connected issues for a given Jira issue.
        This includes parent issues, subtasks, and their respective connections,
        forming a connected component in the issue graph.

        Args:
            issue_key (str): The key of the Jira issue to fetch connected issues for.

        Returns:
            list: A list of connected JiraBaseIssue objects.

        Raises:
            IssueNotFoundException: If the initial issue_key is not found in the repository.
        """
        starting_issue = self.get_issue_by_key(issue_key)

        queue = collections.deque([starting_issue.key])
        seen_issue_keys: Set[str] = {starting_issue.key}

        connected_issue_objects: List[JiraBaseIssue] = []

        while queue:
            current_issue_key = queue.popleft()
            current_issue = self._issue_repository.get_issue(current_issue_key)

            if current_issue is None:
                continue

            connected_issue_objects.append(current_issue)

            # Check for 'parent_key' attribute on the current issue
            # JiraBaseIssue itself doesn't have parent_key by default,
            # but JiraSubtask does. We need to check if the attribute exists.
            if hasattr(current_issue, 'parent_key') and current_issue.parent_key:
                parent_key = getattr(current_issue, "parent_key")
                if parent_key and parent_key not in seen_issue_keys:
                    seen_issue_keys.add(parent_key)
                    queue.append(parent_key)

            # Check for 'subtasks' attribute on the current issue
            # JiraBaseIssue has 'subtasks' field, so direct access is fine.
            for subtask_key in current_issue.subtasks:
                if subtask_key not in seen_issue_keys:
                    seen_issue_keys.add(subtask_key)
                    queue.append(subtask_key)

        connected_issue_objects.sort(key=lambda issue: issue.key)
        return connected_issue_objects

def connected_issues_for_key(issue_key: str) -> List[JiraBaseIssue]:
    """
    Fetches all connected issues for a given issue key.
    
    Args:
        issue_key (str): The key of the Jira issue to fetch connected issues for.
    
    Returns:
        List[JiraBaseIssue]: A list of connected JiraBaseIssue objects.
    """
    # 1. Initialize the Jira Handler
    jira_api_client = JiraHandler()

    # 2. Fetch all relevant issues once and build the repository
    # This assumes "project=DATA" fetches all issues that might be connected.
    # In a real-world scenario, you might fetch issues for specific projects
    # or use more targeted JQL if the graph of connections is too large.
    all_project_issues = jira_api_client.fetch_and_parse_issues(jql="project=DATA")

    # 3. Create the IssueRepository for efficient lookups
    issue_repo = IssueRepository(all_project_issues)

    # 4. Create the JiraIssueService with its dependencies
    issue_service = JiraIssueService(jira_api_client, issue_repo)

    # Example 1: Get connected issues for DATA-1
    connected_issues_for_data = issue_service.get_connected_issues(issue_key)

    return connected_issues_for_data