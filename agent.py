"""
This module contains parameterized tools to query JIRA data from the database.
Each tool is responsible for querying a specific column from a defined table using safe SQL construction.
"""

import sys
from config import Config
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from langchain_openai import AzureChatOpenAI
from agent_utils import tool_list
from lib.logger import agent_logger as logger

checkpointer = InMemorySaver()
store = InMemoryStore()

config = Config.load_from_env()

model = AzureChatOpenAI(
    azure_deployment="gpt-4o-mini",
    azure_endpoint=config.openai_base_url,
    api_version=config.openai_api_version,
    model_name="gpt-4o-mini"
)

# --- LangGraph Agent Setup ---

service_agent = create_react_agent(
    model=model,
    tools=tool_list,
    name="jira_query_agent",
    prompt="""You are a JIRA expert.
    You can help users query the JIRA database using tools that accept single parameters like assignee, project, or status.
    Use the tools to answer the user's question with relevant data."""
)

workflow = create_supervisor(
    [service_agent],
    model=model,
    prompt=(
        "You are a JIRA expert. You can help the user by using the following tools:\n"
        "- get_tasks_by_assignee(assignee: str)\n"
        "- get_tasks_by_project(project: str)\n"
        "- get_bugs_by_status(status: str)\n"
        "- get_subtasks_by_parent_key(parent_key: str)\n"
        "- get_tasks_by_text_similarity(text: str)\n"
        "All tools query one of the following tables: jira_task, jira_subtask, or jira_bug.\n"
        "Use them to retrieve information like key, status_category, and assignee."
    ),
    output_mode="full_history"
)

app = workflow.compile(
    checkpointer=checkpointer,
    store=store
)

config = {"configurable": {"thread_id": "thread-1"}}

def main():
    """
    Main function to run the agent and process user input.
    """
    if len(sys.argv) > 1:
        query = sys.argv[1]
    else:
        query = "Which tasks are related to expoloring the Agent Use Cases"

    result = app.invoke({
        "messages": [
            {
                "role": "user",
                "content": query
            }
        ]
    }, config=config)

    for m in result["messages"]:
        m.pretty_print()

if __name__ == "__main__":
    main()
