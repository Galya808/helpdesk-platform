from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
)

Content = Annotated[str, Field(min_length=1, max_length=5000)]


class CommentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: Content

    @field_validator("content", mode="before")
    @classmethod
    def normalize_content(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()

        return value


class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    ticket_id: UUID
    author_id: UUID
    content: Content
    created_at: datetime


class CommentListQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class CommentPage(BaseModel):
    items: list[CommentRead]
    page: int
    page_size: int
    total: int

    @computed_field  # type: ignore[prop-decorator]
    @property
    def pages(self) -> int:
        return (self.total + self.page_size - 1) // self.page_size
