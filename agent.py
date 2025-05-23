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
    prompt="""You are a JIRA expert and want to tell the user as much information as possible.
    Just use the tool get_complete_issue if you already know the issue and can hand over the complete model.
    Use this tool always if the user asks to get the complete issue model, for example comment data, latest authors and worklog activities.
    You can get issue_keys from the tool keyword_search.
    Use the tool connected_issues_for_key for get a list of all issues belonging to the passed issue.
    For example, you can pass that list to the tool get_complete_issue to get all information about all connected issues.
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

default_config = {"configurable": {"thread_id": "thread-1"}}

class JiraAgent:
    def __init__(self, config=default_config):
        self.app = app
        self.config = config
        self.messages = []

    def chat(self, user_input):
        self.messages.append({"role": "user", "content": user_input})
        result = self.app.invoke({"messages": self.messages}, config=self.config)
        agent_reply = result["messages"][-1].content
        self.messages.append({"role": "assistant", "content": agent_reply})
        return agent_reply

    def get_history(self):
        return self.messages

def main():
    agent = JiraAgent()
    while True:
        user_input = input("Du: ")
        if user_input.lower() in ("exit", "quit"):
            break
        agent_reply = agent.chat(user_input)
        print("Agent:", agent_reply)

if __name__ == "__main__":
    main()
