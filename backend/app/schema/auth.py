import re

from pydantic import BaseModel, Field, field_validator

from app.schema.base import CamelModel

_USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=8, max_length=72)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not _USERNAME_PATTERN.match(v):
            raise ValueError("username may only contain letters, digits, and underscores")
        return v


class RegisterResponse(BaseModel):
    id: int
    username: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    token: str


class MemberResponse(CamelModel):
    id: int
    username: str
    is_admin: bool
