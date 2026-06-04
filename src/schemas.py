from datetime import date
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Schema for user registration request."""

    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user data in API responses."""

    id: int
    username: str
    email: EmailStr
    avatar: str | None
    confirmed: bool
    role: str

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Schema for JWT access + refresh token response."""

    access_token: str
    refresh_token: str
    token_type: str


class TokenRefreshRequest(BaseModel):
    """Schema for refresh token request body."""

    refresh_token: str


class RequestPasswordReset(BaseModel):
    """Schema for password reset email request."""

    email: EmailStr


class ConfirmPasswordReset(BaseModel):
    """Schema for password reset confirmation."""

    token: str
    new_password: str


class DemoAccountResponse(BaseModel):
    """Schema for a demo account returned by the bootstrap endpoint."""

    username: str
    email: EmailStr
    password: str
    role: str


class DemoAccountsResponse(BaseModel):
    """Schema for demo account bootstrap response."""

    message: str
    accounts: list[DemoAccountResponse]


class ContactCreate(BaseModel):
    """Schema for creating a contact."""

    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    birthday: date | None = None
    notes: str | None = None


class ContactUpdate(BaseModel):
    """Schema for updating a contact (all fields optional)."""

    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    birthday: date | None = None
    notes: str | None = None


class ContactResponse(BaseModel):
    """Schema for contact data in API responses."""

    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    birthday: date | None
    notes: str | None

    model_config = {"from_attributes": True}


class ContactSearchResponse(BaseModel):
    """Schema for contact search results."""

    message: str
    count: int
    contacts: list[ContactResponse]


class MessageResponse(BaseModel):
    """Schema for simple message responses."""

    message: str
