from langchain_core.tools import tool
from .services import get_calendar_service, list_events, create_event, delete_event, update_event
from .schemas import ListEventsSchema, DeleteEventsSchema, UpdateEventsSchema, CreateEventsSchema

@tool(args_schema=ListEventsSchema)
def list_events_tool(
    start_date: str,
    end_date: str | None = None,
    specific_time: str | None = None,
    time_start: str | None = None,
    time_end: str | None = None,
    include_past: bool = False
) -> dict:
    """
    Get calendar events.
    """

    service = get_calendar_service()

    return list_events(
        service=service,
        date_str=start_date,
        end_date_str=end_date,
        specific_time=specific_time,
        time_start=time_start,
        time_end=time_end,
        include_past=include_past
    )

@tool(args_schema = CreateEventsSchema)
def create_event_tool(
    date: str,
    title: str,
    time: str,
    duration_minutes: int = 60
) -> dict:
    """
    Create a calendar event.
    date: YYYY-MM-DD
    time: HH:MM (24h)
    """

    service = get_calendar_service()
    return create_event(service, date, title, time, duration_minutes)


@tool(args_schema= DeleteEventsSchema)
def delete_event_tool(event_id: str, confirm: bool = False) -> dict:
    """
    Delete an event using its event_id.
    """
    if not confirm:
        return {
            "response_type": "confirmation_needed",
            "message": f"Are you sure you want to delete the event with ID {event_id}? Please confirm."
        }
    
    service = get_calendar_service()
    return delete_event(service, event_id)


@tool(args_schema= UpdateEventsSchema)
def update_event_tool(
    event_id: str,
    new_title: str | None = None,
    new_date: str | None = None,
    new_time: str | None = None,
    duration_minutes: int = 60
) -> dict:
    """
    Update an event.
    """

    service = get_calendar_service()
    return update_event(
        service,
        event_id=event_id,
        new_title=new_title,
        new_date=new_date,
        new_time=new_time,
        duration_minutes=duration_minutes,
    )
