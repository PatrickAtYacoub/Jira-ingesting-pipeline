"""
This module contains functions to create and drop tables in the database.
It uses the `VectorDB` class to execute SQL commands for creating and dropping
tables related to Jira issues and subtasks.
It also includes logging to track the success or failure of these operations.
"""
from tempfile import NamedTemporaryFile
from typing import List
from jira_tools import JiraHandler, JiraIngestor, AttachementHandler
from db import VectorDB, DBConfig
from lib.logger import logger
from model import JiraStory


# ------------------------------------------------------------------------------
# Main Execution
# ------------------------------------------------------------------------------
def main():
    """
    Main function to fetch Jira issues, process them, and ingest them into the database.
    """

    handler = JiraHandler()
    parsed_issues = handler.fetch_and_parse_issues(jql="project=KUNPORT")
    categorized_issues = handler.categorize_issues(parsed_issues)
    jira_client = handler.get_client()

    stories = categorized_issues["stories"]
    subtasks = categorized_issues["subtasks"]
    tasks = categorized_issues["tasks"]
    bugs = categorized_issues["bugs"]
    epics = categorized_issues["epics"]

    logger.info(
        "Epics %d, Stories: %d, Tasks %d, Subtasks: %d, Bugs: %d, Total: %d",
        len(epics),
        len(stories),
        len(tasks),
        len(subtasks),
        len(bugs),
        len(epics) + len(stories) + len(tasks) + len(subtasks) + len(bugs),
    )

    # import json
    # issue_data167 = [
    #     issue for issue in parsed_issues if issue.key == "DATA-167"
    # ][0]

    # return
    # attachement_hdlr = AttachementHandler(jira_client)
    # print(json.dumps(attachement_hdlr.process_attachements(
    #     issue_data167, save_file=True
    # )))
    # for categorized_issues in parsed_issues:
    #     attachement_hdlr.process_attachements(
    #         categorized_issues, save_file=True
    #     )


    # Initialize DB and ingest
    # db_client = VectorDB(
    #     DBConfig(
    #         dbname=config.pg_dbname,
    #         user=config.pg_user,
    #         password=config.pg_password,
    #         host=config.pg_host,
    #     )
    # )

    print("Hallo Hallo")

    jwt_openwebui_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImVjOTZjNTA5LWUyNTItNDk1MC04NTM2LTczNjE0NDZkZTVlYSJ9.oTplyJd-wK90kObA02RYBrw_AVLL2t9SKiNFAsw-7WM"

    import requests

    def upload_file(token, filename, content):
        url = 'http://localhost:3000/api/v1/files/'
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
        #files = {'file': open(file_path, 'rb')}
        files = {'file': (filename, content)}
        response = requests.post(url, headers=headers, files=files)

        # knowledge_id = "54efcd40-4e78-4526-a609-f8bc05ac5800"
        knowledge_id = "6a9f02cc-5f3f-46f2-9ef1-5997f56f4cc6"

        url = f'http://localhost:3000/api/v1/knowledge/{knowledge_id}/file/add'
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        data = {'file_id': response.json()["id"]}
        response = requests.post(url, headers=headers, json=data)
        return response.json()

    # Import the first issue as file
    if stories:
        story: JiraStory
        for story in stories:
            # file_path = first_story.get_attachment_path()
            # with NamedTemporaryFile(suffix=".txt") as temp_file:
            #     temp_file.write(first_story.description.encode('utf-8'))
            #     temp_file.flush()
            try:
                content = story.description

                for subtask in story.subtasks:
                    content += f"\n\nSubtask: {subtask.summary}\n{s.description}"

                response = upload_file(jwt_openwebui_key, story.key + story.summary + ".txt", content.encode('utf-8'))
            except Exception as e:
                print(f"Error uploading file: {e}")

    if epics:
        for epic in epics:
            try:
                content = epic.description

                for story in epic.stories:
                    content += f"\n\nStory: {story.summary}\n{story.description}"

                response = upload_file(jwt_openwebui_key, epic.key + epic.summary + ".txt", content.encode('utf-8'))
            except Exception as e:
                print(f"Error uploading file: {e}")
    # ingestor = JiraIngestor(db_client)
    # ingestor.ingest_bulk(epics=epics, stories=stories, subtasks=subtasks, bugs=bugs, tasks=tasks)




# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------


def print_issues(title: str, issues: List):
    """
    Print a list of issues with a given title.
    """
    print(f"\n{title}:")
    for issue in issues:
        print(issue.to_string(detailed=True))


# ------------------------------------------------------------------------------
# Entry Point
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
