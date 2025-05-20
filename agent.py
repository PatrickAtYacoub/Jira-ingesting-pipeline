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
from ai.prompt_store import PromptStore

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
   """
)

workflow = create_supervisor(
    [service_agent],
    model=model,
    prompt=(
        PromptStore.get_prompt(
            "jira_support",
            object="jira_reporting",
            goal="information",
            detail_level="concise",
            recipient="jira_beginner",
            context=["high_information_density", "exact_information"],
        )
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
