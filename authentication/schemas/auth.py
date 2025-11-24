import datetime
from typing import Optional
from uuid import UUID

from pydantic import EmailStr, model_validator

from ..core.base import BaseModel


class EmailLogin(BaseModel):
    email: EmailStr
    password: str


class PasswordValidate(BaseModel):
    password: str
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class EmailRegister(PasswordValidate):
    email: EmailStr
    send_verification_email: Optional[bool] = True


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


class ResetPassword(PasswordValidate):
    token: str


class JWTPayload(BaseModel):
    sub: str
    exp: int
    iat: int
    type: str
