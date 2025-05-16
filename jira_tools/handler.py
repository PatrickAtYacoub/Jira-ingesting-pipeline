import logging
import os
from typing import List, Dict, Type, Any
from jira import JIRA
from model.jira_models import (
    JiraStory,
    JiraSubtask,
    JiraBug,
    JiraTask,
    JiraEpic,
    JiraBaseIssue,
)
from jira_tools import JiraFactory
from lib.logger import logger
from config import Config

def fetch_issues(jira_client: JIRA, jql: str) -> List[Any]:
    issues = []
    start_at = 0
    max_results = 50
    while True:
        batch = jira_client.search_issues(jql, startAt=start_at, maxResults=max_results)
        if not batch:
            break
        issues.extend(batch)
        if len(batch) < max_results:
            break
        start_at += max_results
    return issues

class JiraHandler:
    def __init__(self):
        self.config = Config.load_from_env()
        self.jira_client = JIRA(
            server=self.config.jira_url,
            basic_auth=(self.config.jira_email, self.config.jira_token)
        )

    def list_projects(self) -> None:
        projects = self.jira_client.projects()
        for project in projects:
            print(f"{project.key}: {project.name}")

    def fetch_and_parse_issues(self, jql: str) -> List[JiraBaseIssue]:
        issues = fetch_issues(self.jira_client, jql=jql)
        parsed_issues = [JiraFactory.create_issue(issue) for issue in issues]
        logger.info("Parsed %d issues", len(parsed_issues))
        return parsed_issues

    def categorize_issues(self, parsed_issues: List[Any]) -> Dict[str, List[Any]]:
        issue_types: Dict[Type, str] = {
            JiraStory: "stories",
            JiraSubtask: "subtasks",
            JiraTask: "tasks",
            JiraBug: "bugs",
            JiraEpic: "epics",
        }
        categorized_issues = {name: [] for name in issue_types.values()}
        for issue in parsed_issues:
            for cls, name in issue_types.items():
                if isinstance(issue, cls):
                    categorized_issues[name].append(issue)
                    break
        return categorized_issues

    def get_client(self) -> JIRA:
        return self.jira_client

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    handler = JiraHandler()
    handler.list_projects()
    parsed_issues = handler.fetch_and_parse_issues(jql="project=DATA")
    categorized_issues = handler.categorize_issues(parsed_issues)
    for category, issues in categorized_issues.items():
        logger.info("%s: %d issues", category, len(issues))