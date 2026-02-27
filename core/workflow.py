from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage, AIMessage
from typing import TypedDict, Annotated
import operator
import json
from google_calendar.tools import list_events_tool, update_event_tool, delete_event_tool, create_event_tool
from google_mail.tools import list_emails_tool, send_email_tool, delete_email_tool, modify_labels_tool
from core.resolvers import resolve_event_from_memory
from google_calendar.tool_config import TOOL_REQUIREMENTS as CALENDAR_TOOL_REQUIREMENTS
from google_mail.tool_config import TOOL_REQUIREMENTS as GMAIL_TOOL_REQUIREMENTS
from datetime import date


DESTRUCTIVE_TOOLS = {"delete_event_tool", "delete_email_tool"}

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    last_events: list[dict] | None
    last_emails: list[dict] | None


tools_dict = {
    "list_events_tool": list_events_tool,
    "update_event_tool": update_event_tool,
    "delete_event_tool": delete_event_tool,
    "create_event_tool": create_event_tool,
    "list_emails_tool": list_emails_tool,
    "send_email_tool": send_email_tool,
    "delete_email_tool": delete_email_tool,
    "modify_labels_tool": modify_labels_tool,
}


TOOL_REQUIREMENTS = {
    **CALENDAR_TOOL_REQUIREMENTS,
    **GMAIL_TOOL_REQUIREMENTS,
}


RESOLVER_FUNCTIONS = {
    "resolve_event_from_memory": resolve_event_from_memory,
}

def _latest_user_text(state: AgentState) -> str:
    for message in reversed(state.get("messages", [])):
        if getattr(message, "type", None) == "human" and isinstance(message.content, str):
            return message.content.strip().lower()
    return ""

def _is_explicit_confirmation(user_text: str) -> bool:
    if not user_text:
        return False

    explicit_confirms = {
        "yes",
        "yes do it",
        "confirm",
        "please confirm",
        "go ahead",
        "proceed",
        "do it",
    }

    return user_text in explicit_confirms or user_text.startswith("yes ")


def _is_missing_arg(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) == 0
    return False


def _extract_tool_payload(message: BaseMessage) -> dict | None:
    artifact = getattr(message, "artifact", None)
    if isinstance(artifact, dict):
        return artifact

    content = getattr(message, "content", None)
    if isinstance(content, dict):
        return content

    if isinstance(content, str):
        try:
            parsed = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return None
        return parsed if isinstance(parsed, dict) else None

    return None


def call_model(state: AgentState, client, tool_node: ToolNode) -> dict:
    today = date.today()

    system_prompt = f"""
Today is {today}

You are a Google Calendar and Gmail assistant.
Follow all tool usage and confirmation rules strictly.
You help users:
- Create, update, delete, and list calendar events
- Send, list, delete, and modify Gmail messages

GENERAL RULES:
- Use tools whenever an action affects Google Calendar or Gmail.
- Never fabricate tool results.
- Never expose raw tool JSON to the user.
- If required information is missing or ambiguous, ask a clarification question.
- Resolve all relative dates (e.g., "tomorrow", "next Monday") before calling tools.
- Normalize all resolved dates and times into full ISO format internally.
- Always confirm completed actions in natural, professional language.
- Always include full resolved date, time, and year in confirmations.

==================================================
CALENDAR RULES
==================================================

---------------------------
DATE RESOLUTION RULES
---------------------------

- If the user does NOT explicitly mention a date:
    → Assume the event is for today (based on the system "Today" variable).

- If the user mentions a date but NOT a year:
    → Assume the current year from the system "Today" variable.

- If a date (without year) has already passed this year:
    → Schedule it for the next occurrence (next year).

- Resolve relative dates (e.g., "tomorrow", "next Monday") before calling tools.

------------------------------------------------
WHEN LISTING EVENTS
------------------------------------------------

Interpret user intent carefully and choose parameters accordingly.

1) If user asks for a SPECIFIC TIME:
   Examples:
   - "What do I have at 5 PM?"
   - "Any meeting at 10:30 AM?"
   
   → Call list_events with:
     specific_time = that exact time
   → Return only events occurring at that time.

2) If user asks for a TIME RANGE:
   Examples:
   - "List events between 3 PM and 6 PM"
   - "What do I have from 1 to 4?"

   → Call list_events with:
     time_start and time_end
   → Return events within that time window only.

3) If user asks to list events WITHOUT mentioning time:
   Example:
   - "List today's events"
   - "What do I have today?"

   → If the date is today:
       Return only UPCOMING events (after current time).
       (include_past = False)
   → If the date is future:
       Return full day.
   → If the date is past:
       Return full day.

4) If user explicitly says:
   - "List all events"
   - "Show full schedule"
   - "Show all meetings today"
   - "Show complete calendar"

   → Return full day (00:00 to 23:59)
   → include_past = True

Always:
- Present events clearly.
- Include title, full date, and time (with year).
- If no events found, say so politely.

------------------------------------------------
WHEN CREATING EVENTS
------------------------------------------------

Required:
- Title
- Date
- Time

Time rules:
- If time is missing → Ask the user.
- If time is vague (e.g., "evening") → Ask for specific hour.

Duration:
- Default duration is 1 hour unless specified.
- If end time provided → calculate automatically.

Conflict Handling:
- Check for overlapping events.
- If conflict exists → inform user and ask how to proceed.

Timezone:
- Always use stored user timezone.
- If unavailable → ask before scheduling.

------------------------------------------------
WHEN UPDATING OR DELETING EVENTS
------------------------------------------------

- If multiple events match → Ask which one.
- If none match → Inform politely.
- Always confirm destructive actions by restating:
  Title + Date + Time.

==================================================
GMAIL RULES
==================================================

WHEN SENDING EMAILS:

Required for send_email_tool:
- to
- subject
- body_text

If body provided but subject missing:
    → Generate concise, relevant subject.

If subject provided but body missing:
    → Generate professional email body.

If neither provided:
    → Ask the user what they want to say.

Formatting:
- Clean and professional.
- Match user's tone.
- Improve vague subjects (e.g., "Hi").

WHEN LISTING EMAILS:
- Show sender, subject, and date clearly.

WHEN DELETING OR MODIFYING EMAILS:
- Confirm clearly after execution.

==================================================
CONFIRMATION STYLE
==================================================

Calendar confirmation example:
"Your meeting has been scheduled for Tuesday, February 25, 2026 at 3:00 PM."

Email confirmation example:
"Your email has been sent to john@example.com with the subject 'Project Update'."

Keep confirmations:
- Clear
- Fully resolved (no relative terms like 'tomorrow')
- Professional
- Concise
"""

    messages = [{"role": "system", "content": system_prompt}] + state["messages"]

    client_with_tools = client.bind_tools(list(tools_dict.values()))
    response = client_with_tools.invoke(messages)

    user_text = _latest_user_text(state)
    is_user_confirmed = _is_explicit_confirmation(user_text)

    if not response.tool_calls:
        return {"messages": [response]}

    updated_tool_calls = []

    for call in response.tool_calls:
        tool_name = call["name"]
        tool_config = TOOL_REQUIREMENTS.get(tool_name)

        updated_call = {
            "id": call.get("id"),
            "name": tool_name,
            "args": dict(call.get("args", {})),
        }

        if tool_name in DESTRUCTIVE_TOOLS:
            if not is_user_confirmed:
                return {
                    "messages": [
                        AIMessage(
                            content="Are you sure you want to proceed? Please confirm by saying 'yes'."
                        )
                    ]
                }
            updated_call["args"]["confirm"] = True

        if tool_config:
            resolvers = tool_config.get("resolvers", {})
            for arg, resolver_name in resolvers.items():
                resolver_fn = RESOLVER_FUNCTIONS.get(resolver_name)
                if resolver_fn:
                    resolved_value = resolver_fn(
                        state,
                        user_text,
                        client,
                    )

                    if resolved_value == "AMBIGUOUS":
                        return {
                            "messages": [
                                AIMessage(
                                    content="Multiple events match that name. Which one would you like to choose?"
                                )
                            ]
                        }

                    if resolved_value:
                        updated_call["args"][arg] = resolved_value

            required_args = tool_config.get("required", [])
            missing_required = [
                required_arg
                for required_arg in required_args
                if _is_missing_arg(updated_call["args"].get(required_arg))
            ]
            if missing_required:
                missing_fields = ", ".join(missing_required)
                return {
                    "messages": [
                        AIMessage(
                            content=(
                                f"I need more details before using `{tool_name}`. "
                                f"Please provide: {missing_fields}."
                            )
                        )
                    ]
                }

        updated_tool_calls.append(updated_call)

    response.tool_calls = updated_tool_calls

    return {"messages": [response]}


def tool_handler(state: AgentState, tool_node: ToolNode):
    result = tool_node.invoke(state)
    tool_messages = result.get("messages", [])

    new_state = {
        "messages": tool_messages,
        "last_events": state.get("last_events"),
        "last_emails": state.get("last_emails"),
    }

    for tool_message in tool_messages:
        payload = _extract_tool_payload(tool_message)
        if not payload:
            continue

        if payload.get("response_type") == "events_list":
            new_state["last_events"] = payload.get("events", [])

        if payload.get("response_type") == "emails_list":
            new_state["last_emails"] = payload.get("emails", [])

    return new_state


def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "tools"
    return END


def build_workflow(client):
    workflow = StateGraph(AgentState)

    tool_node = ToolNode(list(tools_dict.values()))

    workflow.add_node("agent", lambda state: call_model(state, client, tool_node))
    workflow.add_node("tools", lambda state: tool_handler(state, tool_node))

    workflow.add_edge(START, "agent")

    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", END: END},
    )

    workflow.add_edge("tools", "agent")

    return workflow.compile()