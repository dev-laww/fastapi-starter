import datetime
from uuid import UUID

from pydantic import EmailStr

from ..core.base import BaseModel


class EmailLogin(BaseModel):
    email: EmailStr
    password: str


class EmailRegister(BaseModel):
    email: EmailStr
    password: str
    confirm_password: str


class AuthUser(BaseModel):
    id: UUID
    email: EmailStr
    email_verified: bool


class AuthSession(BaseModel):
    id: UUID
    expires_at: datetime.datetime


class AuthResponse(BaseModel):
    user: AuthUser
    session: AuthSession
    access_token: str
    token_type: str = "bearer"
