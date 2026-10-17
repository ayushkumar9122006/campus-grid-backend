from datetime import datetime
from typing import Optional
from pydantic import Field, field_validator

from campus_grid.model.user import UserRole
from campus_grid.schema.base_schema import BaseSchema


class UserRegister(BaseSchema):
    email: str = Field(..., description="Valid institutional email address")
    password: str = Field(..., min_length=8, description="Password minimum 8 characters")
    role: UserRole = Field(default=UserRole.STUDENT, description="Assigned role: student, faculty, admin")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        clean = v.strip().lower()
        if "@" not in clean or "." not in clean.split("@")[-1]:
            raise ValueError("Invalid email format")
        return clean

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class UserLogin(BaseSchema):
    email: str = Field(..., description="Registered email address")
    password: str = Field(..., description="Account password")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserResponse(BaseSchema):
    id: int
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserRoleUpdate(BaseSchema):
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
