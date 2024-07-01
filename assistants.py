from datetime import datetime

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.runnables import ensure_config
from agent import llm
from state import State
from tools import lookup_policy


class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        while True:
            result = self.runnable.invoke(state)

            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}


class CompleteOrEscalate(BaseModel):
    """A tool to mark the current task as completed and/or to escalate control of the dialog to the main assistant,
    who can re-route the dialog based on the user's needs."""

    cancel: bool = True
    reason: str

    class Config:
        schema_extra = {
            "example": {
                "cancel": True,
                "reason": "User changed their mind about the current task.",
            },
            "example 2": {
                "cancel": True,
                "reason": "I have fully completed the task.",
            },
            "example 3": {
                "cancel": False,
                "reason": "I need to search the user's emails or calendar for more information.",
            },
        }


config = ensure_config()  # Fetch from the context
configuration = config.get("configurable", {})
language_id = configuration.get("language", None)
if not language_id:
    print("No language configured.")
primary_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful customer support assistant for solving Health, Safety and Nutrition issues during Hajj. " 
            f"Speak to the customer in a language={language_id}. "
            "Greet the customer. Tell them who you are and offer help. Be polite."             
            "Your primary role is to search for necessary information to answer customer queries. "             
            "If a customer requests  help with getting food or water, getting medical assistance, getting safety recommendations. " 
            "If a customer does not give enough information about getting food or water, getting medical assistance, getting safety recommendations - ask for further details. "             
            "Provide detailed information to the customer, and always double-check the database before concluding that information is unavailable. "             
            "When searching, be persistent. Expand your query bounds if the first search returns no results. "             
            "If a search comes up empty, expand your search before giving up.",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now())
primary_assistant_tools = [
    lookup_policy,
    # TavilySearchResults(max_results=1, api_wrapper=tavilySearchAPIWrapper, include_domains=['www.arabnews.com']),
]
assistant_runnable = primary_assistant_prompt | llm.bind_tools(
    primary_assistant_tools
)
