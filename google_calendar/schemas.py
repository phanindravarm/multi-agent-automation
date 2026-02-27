from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from datetime import datetime

class ListEventsSchema(BaseModel):
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: Optional[str] = Field(None, description="End date in YYYY-MM-DD format")
    specific_time: Optional[str] = Field(None, description="Specific time in HH:MM 24h format")
    time_start: Optional[str] = Field(None, description="Start of time range in HH:MM 24h format")
    time_end: Optional[str] = Field(None, description="End of time range in HH:MM 24h format")
    include_past: bool = Field(False, description="Include past events today")

    @field_validator("start_date", "end_date")
    def validate_dates(cls, v):
        if v is None:
            return v
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v

    @field_validator("specific_time", "time_start", "time_end")
    def validate_times(cls, v):
        if v is None:
            return v
        try:
            datetime.strptime(v, "%H:%M")
        except ValueError:
            raise ValueError("Time must be in HH:MM 24-hour format")
        return v

    @model_validator(mode="after")
    def validate_time_filters(self):
        has_specific = self.specific_time is not None
        has_start = self.time_start is not None
        has_end = self.time_end is not None

        if has_specific and (has_start or has_end):
            raise ValueError("specific_time cannot be combined with time_start/time_end")

        if has_start != has_end:
            raise ValueError("time_start and time_end must be provided together")

        if has_start and has_end:
            start = datetime.strptime(self.time_start, "%H:%M")
            end = datetime.strptime(self.time_end, "%H:%M")
            if start >= end:
                raise ValueError("time_start must be earlier than time_end")

        return self


class CreateEventsSchema(BaseModel):
    date: str = Field(..., description="Event date in YYYY-MM-DD format")
    title: str = Field(..., description="Event title, 3-100 chars")
    time: str = Field(..., description="Event start time HH:MM 24h format")
    duration_minutes: int = Field(60, ge=5, le=480, description="Duration in minutes (5-480)")

    @field_validator("date")
    def validate_date(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be YYYY-MM-DD")
        return v

    @field_validator("time")
    def validate_time(cls, v):
        try:
            datetime.strptime(v, "%H:%M")
        except ValueError:
            raise ValueError("Time must be HH:MM 24-hour format")
        return v

class DeleteEventsSchema(BaseModel):
    event_id: str = Field(..., description="ID of the event to delete")
    confirm: Optional[bool] = Field(False, description="Require confirmation before deletion")

class UpdateEventsSchema(BaseModel):
    event_id: str = Field(..., description="ID of the event to update")
    new_title: Optional[str] = Field(None, description="New title for the event")
    new_date: Optional[str] = Field(None, description="New date YYYY-MM-DD")
    new_time: Optional[str] = Field(None, description="New start time HH:MM 24h format")
    duration_minutes: Optional[int] = Field(60, ge=5, le=480, description="Duration in minutes (5-480)")

    @field_validator("new_date")
    def validate_new_date(cls, v):
        if v is None:
            return v
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be YYYY-MM-DD")
        return v

    @field_validator("new_time")
    def validate_new_time(cls, v):
        if v is None:
            return v
        try:
            datetime.strptime(v, "%H:%M")
        except ValueError:
            raise ValueError("Time must be HH:MM 24-hour format")
        return v
