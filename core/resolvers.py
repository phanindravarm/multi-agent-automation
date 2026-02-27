from datetime import date
from typing import Any

def resolve_event_from_memory(state: dict, user_input: str, client: Any) -> str | None:
    """
    Resolves the event_id from the last fetched events stored in state.
    Returns 'AMBIGUOUS' if multiple matches found.
    """
    last_events = state.get("last_events")
    if not last_events:
        return None

    user_input_lower = user_input.lower()

    matches = [
        e for e in last_events
        if e["summary"].lower() in user_input_lower
        or e["start_time"].lower() in user_input_lower
    ]

    if len(matches) == 1:
        return matches[0]["id"]

    if len(matches) > 1:
        return "AMBIGUOUS"

    return None
