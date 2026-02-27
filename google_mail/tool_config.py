TOOL_REQUIREMENTS = {
    "list_emails_tool": {
        "required": [],  
        "resolvers": {}
    },
    "send_email_tool": {
        "required": ["to"],
        "resolvers": {}
    },
    "delete_email_tool": {
        "required": ["message_id"],
        "resolvers": {}
    },
    "modify_labels_tool": {
        "required": ["message_id"],
        "resolvers": {}
    }
}
