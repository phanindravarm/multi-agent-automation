from langchain_core.tools import tool
from .services import get_gmail_service, list_emails, send_email, delete_email, modify_labels
from .schemas import ListEmailsSchema, SendEmailSchema, DeleteEmailSchema, ModifyLabelsSchema

@tool(args_schema=ListEmailsSchema)
def list_emails_tool(label_ids: list[str] | None = None, max_results: int = 10) -> dict:
    """List emails from Gmail"""
    service = get_gmail_service()
    return list_emails(service, label_ids=label_ids, max_results=max_results)


@tool(args_schema=SendEmailSchema)
def send_email_tool(to: str, subject: str | None = None, body_text: str | None = None) -> dict:
    """Send emails from Gmail"""
    service = get_gmail_service()
    return send_email(service, to, subject, body_text)


@tool(args_schema=DeleteEmailSchema)
def delete_email_tool(message_id: str, confirm: bool = False) -> dict:
    """Delete an email by ID"""
    if not confirm:
        return {
            "response_type": "confirmation_needed",
            "message": f"Are you sure you want to delete the message with ID {message_id}? Please confirm."
        }
    service = get_gmail_service()
    return delete_email(service, message_id)


@tool(args_schema=ModifyLabelsSchema)
def modify_labels_tool(
    message_id: str,
    labels_to_add: list[str] | None = None,
    labels_to_remove: list[str] | None = None
) -> dict:
    """Add or remove labels on an email"""
    service = get_gmail_service()
    return modify_labels(service, message_id, labels_to_add, labels_to_remove)