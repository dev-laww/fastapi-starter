import datetime
from typing import Optional
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


class CallbackBase(BaseModel):
    callback_url: Optional[str] = None


class VerifyEmail(CallbackBase):
    token: str


class EmailWithCallback(CallbackBase):
    email: EmailStr


class ResetPassword(BaseModel):
    token: str
    password: str
    confirm_password: str
