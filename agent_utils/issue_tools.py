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

class JiraIssueResponse(BaseModel):
    # Accept all fields dynamically
    class Config:
        extra = "allow"

def get_complete_issue(issue_key: str) -> JiraIssueResponse:
    
    """
    Returns the complete Issue Model for a given Jira issue from the Jira API.
    
    Args:
        issue_key (str): The key of the Jira issue to fetch.
    
    Returns:
        JiraIssueResponse: JSON Model of the complete issue.
    """
    conf = Config.load_from_env()
    user = conf.jira_email
    token = conf.jira_token
    url = f"https://me-easy.atlassian.net/rest/api/2/issue/{issue_key}"

    # Basic Auth header: base64("email:api_token")
    auth_str = f"{user}:{token}"
    b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")

    headers = {
        "Accept": "application/json",
        "Authorization": f"Basic {b64_auth}",
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return JiraIssueResponse.model_validate(response.json())
    else:
        raise Exception(f"Failed to fetch issue details: {response.status_code} - {response.text}")