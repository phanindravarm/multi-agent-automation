from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from email.utils import parseaddr


class ListEmailsSchema(BaseModel):
    label_ids: Optional[List[str]] = Field(None, description="List of Gmail label IDs to filter emails")
    max_results: int = Field(10, ge=1, le=100, description="Maximum number of emails to return (1-100)")

class SendEmailSchema(BaseModel):
    to: str = Field(..., description="Recipient email address")
    subject: Optional[str] = Field(None, description="Email subject")
    body_text: Optional[str] = Field(None, description="Email body text")

    @field_validator("to")
    def validate_email(cls, v):
        if "@" not in parseaddr(v)[1]:
            raise ValueError(f"Invalid email address: {v}")
        return v

class DeleteEmailSchema(BaseModel):
    message_id: str = Field(..., description="Gmail message ID to delete")
    confirm: bool = Field(False, description="Set True to confirm deletion")


class ModifyLabelsSchema(BaseModel):
    message_id: str = Field(..., description="Gmail message ID to modify labels")
    labels_to_add: Optional[List[str]] = Field(None, description="Labels to add")
    labels_to_remove: Optional[List[str]] = Field(None, description="Labels to remove")