from auth import authenticate_google_account
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64

def get_gmail_service():
    creds = authenticate_google_account()
    return build("gmail", "v1", credentials=creds)


def list_emails(service, label_ids=None, max_results=10):
    """
    List emails in the user's mailbox.
    :param label_ids: List of Gmail label IDs to filter emails, e.g., ['INBOX']
    :param max_results: Max number of emails to return
    """
    try:
        results = service.users().messages().list(
            userId="me",
            labelIds=label_ids or ["INBOX"],
            maxResults=max_results
        ).execute()
        messages = results.get("messages", [])

        email_list = []
        for msg in messages:
            msg_detail = service.users().messages().get(
                userId="me", id=msg["id"], format="metadata", metadataHeaders=["From", "Subject", "Date"]
            ).execute()

            headers = {h["name"]: h["value"] for h in msg_detail.get("payload", {}).get("headers", [])}
            email_list.append({
                "id": msg["id"],
                "from": headers.get("From"),
                "subject": headers.get("Subject", "No Subject"),
                "date": headers.get("Date")
            })

        return {
            "response_type": "emails_list",
            "emails": email_list
        }

    except Exception as e:
        return {
            "response_type": "error",
            "error": str(e)
        }


def send_email(service, to, subject, body_text):
    """
    Send an email via Gmail.
    """
    try:
        safe_subject = subject or "No Subject"
        safe_body = body_text or ""
        message = MIMEText(safe_body)
        message["to"] = to
        message["subject"] = safe_subject

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        message_body = {"raw": raw_message}

        sent_message = service.users().messages().send(
            userId="me",
            body=message_body
        ).execute()

        return {
            "response_type": "email_sent",
            "message_id": sent_message.get("id"),
            "to": to,
            "subject": safe_subject
        }

    except Exception as e:
        return {
            "response_type": "error",
            "error": str(e)
        }


def delete_email(service, message_id):
    """
    Delete an email by ID.
    """
    try:
        service.users().messages().delete(
            userId="me",
            id=message_id
        ).execute()

        return {
            "response_type": "email_deleted",
            "message_id": message_id
        }

    except Exception as e:
        return {
            "response_type": "error",
            "error": str(e)
        }


def modify_labels(service, message_id, labels_to_add=None, labels_to_remove=None):
    """
    Modify labels for an email.
    """
    try:
        body = {
            "addLabelIds": labels_to_add or [],
            "removeLabelIds": labels_to_remove or []
        }
        updated_msg = service.users().messages().modify(
            userId="me",
            id=message_id,
            body=body
        ).execute()

        return {
            "response_type": "labels_updated",
            "message_id": message_id,
            "labels": updated_msg.get("labelIds", [])
        }

    except Exception as e:
        return {
            "response_type": "error",
            "error": str(e)
        }
