from auth import authenticate_google_account
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from dateutil import parser
import pytz

TIMEZONE = "Asia/Kolkata"

def get_calendar_service():
    creds = authenticate_google_account()
    return build("calendar", "v3", credentials=creds)


def list_events(
    service,
    date_str: str,
    end_date_str: str = None,
    specific_time: str = None,      # "15:00"
    time_start: str = None,         # "15:00"
    time_end: str = None,           # "18:00"
    include_past: bool = False
) -> dict:

    try:
        local_tz = pytz.timezone(TIMEZONE)
        now = datetime.now(local_tz)

        start_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        end_date = (
            datetime.strptime(end_date_str, "%Y-%m-%d").date()
            if end_date_str else start_date
        )

        # Default full-day range
        day_start = local_tz.localize(datetime.combine(start_date, datetime.min.time()))
        day_end = local_tz.localize(
            datetime.combine(end_date + timedelta(days=1), datetime.min.time())
        )

        # CASE 1: Specific time
        if specific_time:
            target_time = local_tz.localize(
                datetime.combine(start_date, datetime.strptime(specific_time, "%H:%M").time())
            )
            time_min = target_time
            time_max = target_time + timedelta(minutes=1)

        # CASE 2: Time range
        elif time_start and time_end:
            time_min = local_tz.localize(
                datetime.combine(start_date, datetime.strptime(time_start, "%H:%M").time())
            )
            time_max = local_tz.localize(
                datetime.combine(start_date, datetime.strptime(time_end, "%H:%M").time())
            )

        # CASE 3: Default listing (post current time)
        elif start_date == now.date() and not include_past:
            time_min = now
            time_max = day_end

        # CASE 4: List all
        else:
            time_min = day_start
            time_max = day_end

        events = service.events().list(
            calendarId="primary",
            timeMin=time_min.isoformat(),
            timeMax=time_max.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        ).execute().get("items", [])

        formatted_events = [
            {
                "summary": e.get("summary", "No Title"),
                "start_time": (
                    parser.parse(e["start"]["dateTime"]).strftime("%Y-%m-%d %I:%M %p")
                    if "dateTime" in e["start"]
                    else "All Day"
                ),
                "id": e.get("id"),
            }
            for e in events
        ]

        return {
            "response_type": "events_list",
            "events": formatted_events,
        }

    except Exception as e:
        return {"response_type": "error", "error": str(e)}

def create_event(
    service,
    date: str,
    title: str,
    time: str,
    duration_minutes: int = 60
) -> dict:
    """
    Create a calendar event.
    """

    try:
        local_tz = pytz.timezone(TIMEZONE)

        start_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        start_dt = local_tz.localize(start_dt)
        end_dt = start_dt + timedelta(minutes=duration_minutes)

        event_body = {
            "summary": title,
            "start": {
                "dateTime": start_dt.isoformat(),
                "timeZone": TIMEZONE,
            },
            "end": {
                "dateTime": end_dt.isoformat(),
                "timeZone": TIMEZONE,
            },
        }

        event = service.events().insert(
            calendarId="primary",
            body=event_body
        ).execute()

        return {
            "response_type": "event_created",
            "event_id": event.get("id"),
            "title": title,
            "date": date,
            "time": time
        }

    except Exception as e:
        return {
            "response_type": "error",
            "error": str(e)
        }   

def delete_event(
    service,
    event_id: str
) -> dict:
    """
    Delete a calendar event by ID.
    """

    try:
        service.events().delete(
            calendarId="primary",
            eventId=event_id
        ).execute()

        return {
            "response_type": "event_deleted",
            "event_id": event_id
        }

    except Exception as e:
        return {
            "response_type": "error",
            "error": str(e)
        }


def update_event(
    service,
    event_id: str,
    new_title: str = None,
    new_date: str = None,
    new_time: str = None,
    duration_minutes: int = 60
) -> dict:
    """
    Update an existing event.
    """

    try:
        event = service.events().get(
            calendarId="primary",
            eventId=event_id
        ).execute()

        local_tz = pytz.timezone(TIMEZONE)

        if new_title:
            event["summary"] = new_title

        if new_date or new_time:
            existing_start = parser.parse(event["start"]["dateTime"])

            date_part = new_date if new_date else existing_start.strftime("%Y-%m-%d")
            time_part = new_time if new_time else existing_start.strftime("%H:%M")

            start_dt = datetime.strptime(
                f"{date_part} {time_part}",
                "%Y-%m-%d %H:%M"
            )
            start_dt = local_tz.localize(start_dt)
            end_dt = start_dt + timedelta(minutes=duration_minutes)

            event["start"]["dateTime"] = start_dt.isoformat()
            event["start"]["timeZone"] = TIMEZONE

            event["end"]["dateTime"] = end_dt.isoformat()
            event["end"]["timeZone"] = TIMEZONE

        updated_event = service.events().update(
            calendarId="primary",
            eventId=event_id,
            body=event
        ).execute()

        return {
            "response_type": "event_updated",
            "event_id": event_id,
            "updated_title": updated_event.get("summary")
        }

    except Exception as e:
        return {
            "response_type": "error",
            "error": str(e)
        }
