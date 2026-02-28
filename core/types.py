from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    """
    Represents the state of the assistant at any given time.
    """
    messages: Annotated[list[BaseMessage], operator.add]  
    last_events: list | None   
    last_emails : list | None
    conversation_summary: str | None
    summarized_message_count: int