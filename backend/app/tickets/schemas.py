from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.tickets.model import TicketPriority, TicketStatus

Title = Annotated[str, Field(min_length=3, max_length=200)]
Description = Annotated[str, Field(min_length=10, max_length=10000)]


class TicketRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: Title
    description: Description
    status: TicketStatus
    priority: TicketPriority
    customer_id: UUID
    assignee_id: UUID | None
    created_at: datetime
    updated_at: datetime


class TicketCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Title
    description: Description
    priority: TicketPriority = TicketPriority.MEDIUM

    @field_validator("title", "description", mode="before")
    @classmethod
    def normalize_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value
