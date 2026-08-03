from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.users.model import UserRole

Password = Annotated[str, Field(min_length=12, max_length=128)]


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    role: UserRole
    is_blocked: bool
    created_at: datetime
    updated_at: datetime


class NormalizedEmailSchema(BaseModel):
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value


class UserCreate(NormalizedEmailSchema):
    password: Password


class UserLogin(NormalizedEmailSchema):
    password: Password
