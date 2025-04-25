from typing import Optional, List, Union
from model.jira_models import JiraUser, JiraWorklog, JiraSubtask, JiraStory

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
        """
        if user:
            return JiraUser(displayName=user.displayName, emailAddress=user.emailAddress)
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
        """
        return [
            JiraWorklog(
                started=w.started,
                timeSpent=w.timeSpent,
                timeSpentSeconds=w.timeSpentSeconds
            ) for w in worklog_obj.worklogs
        ] if hasattr(worklog_obj, "worklogs") else []

    @staticmethod
    def create_issue(issue) -> Union[JiraSubtask, JiraStory]:
        """
        Create a Jira issue object (subtask or story) from a Jira issue.
        Args:
            issue: The Jira issue object to create from.
        Returns:
            Union[JiraSubtask, JiraStory]: A JiraSubtask instance if the issue 
            is a subtask, otherwise a JiraStory instance.
        """
        fields = issue.fields
        base_kwargs = dict(
            key=issue.key,
            summary=fields.summary,
            description=fields.description if fields.description else "No description",
            status=fields.status.name,
            statusCategory=fields.status.statusCategory.name,
            project=fields.project.name,
            issue_type=fields.issuetype.name,
            assignee=JiraFactory.parse_user(fields.assignee),
            reporter=JiraFactory.parse_user(fields.reporter),
            created=fields.created,
            updated=fields.updated,
            timeSpentSeconds=fields.timespent,
            url=issue.self,
            worklogs=JiraFactory.parse_worklogs(fields.worklog)
        )

        if fields.issuetype.subtask:
            return JiraSubtask(
                **base_kwargs,
                parent_key=fields.parent.key,
                parent_summary=fields.parent.fields.summary
            )
        else:
            return JiraStory(
                **base_kwargs
            )
