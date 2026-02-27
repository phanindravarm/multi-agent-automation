TOOL_REQUIREMENTS = {
    "delete_event_tool": {
        "required": ["event_id"],
        "resolvers": {
            "event_id": "resolve_event_from_memory"
        }
    },
    "update_event_tool": {
        "required": ["event_id"],
        "resolvers": {
            "event_id": "resolve_event_from_memory"
        }
    },
    "list_events_tool": {
        "required": ["start_date"],
    },
    "create_event_tool": {
        "required": ["date", "title", "time"],
        "resolvers": {}
    }
}

