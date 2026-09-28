"""Pydantic schemas for authentication, registration, and user profiles."""

import re
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class UserRegisterRequest(BaseModel):
    """Payload for registering a new user account."""

    email: EmailStr = Field(description="User's institutional or personal email address")
    password: str = Field(min_length=8, max_length=128, description="Plaintext password meeting complexity policy")
    full_name: str = Field(min_length=2, max_length=100, description="Full legal or preferred name")
    phone: Optional[str] = Field(default=None, max_length=30, description="Optional contact phone number")
    role: Optional[str] = Field(default="STUDENT", description="Initial role assignment (defaults to STUDENT)")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[\W_]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserLoginRequest(BaseModel):
    """Payload for authenticating with username/email and password."""

    email: str = Field(description="Normalized email address")
    password: str = Field(description="Account password")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v


class UserResponse(BaseModel):
    """Serialized public user profile. Strictly excludes password and hashes."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    phone: Optional[str] = None
    is_active: bool
    is_verified: bool
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    created_at: datetime
    last_login_at: Optional[datetime] = None

    @model_validator(mode="before")
    @classmethod
    def extract_from_user(cls, data: Any) -> Any:
        if hasattr(data, "__table__"):
            return {
                "id": str(data.id),
                "email": data.email,
                "full_name": data.full_name,
                "phone": data.phone,
                "is_active": data.is_active,
                "is_verified": data.is_verified,
                "roles": [r.name for r in getattr(data, "roles", [])],
                "permissions": sorted(list(data.permission_codes)) if hasattr(data, "permission_codes") else [],
                "created_at": data.created_at,
                "last_login_at": data.last_login_at,
            }
        return data


class TokenResponse(BaseModel):
    """Response payload containing access token metadata and user profile."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Optional payload for refreshing session tokens when not using cookies."""

    refresh_token: Optional[str] = None


class MessageResponse(BaseModel):
    """Generic status or success message response."""

    message: str


class UserRoleUpdateRequest(BaseModel):
    """Payload for administrative assignment or modification of user roles."""

    roles: List[str] = Field(min_length=1, description="List of system role names to assign to user")

