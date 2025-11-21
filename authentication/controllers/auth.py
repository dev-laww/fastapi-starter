from typing import Annotated

from fastapi import Depends, Request
from starlette.responses import Response

from ..core import settings
from ..core.base import Controller
from ..core.database import Repository
from ..core.database.repository import get_repository
from ..core.exceptions import (
    AuthenticationError,
    NoImplementationError,
    ValidationError,
)
from ..core.response import Response as AppResponse
from ..models import User
from ..schemas.auth import (
    EmailLogin,
    EmailRegister,
    AuthResponse,
    AuthUser,
    AuthSession,
)
from ..services import AccountService, SessionService


class AuthController(Controller):
    def __init__(
        self,
        user_repository: Annotated[Repository[User], Depends(get_repository(User))],
        account_service: Annotated[AccountService, Depends()],
        session_service: Annotated[SessionService, Depends()],
    ):
        self.user_repository = user_repository
        self.account_service = account_service
        self.session_service = session_service

    async def login(self, data: EmailLogin, request: Request, response: Response):
        account = await self.account_service.verify_credential(
            email=str(data.email), password=data.password
        )

        if not account:
            raise AuthenticationError("Invalid email or password")

        user = await self.user_repository.get_or_raise(account.user_id)

        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        session = await self.session_service.create_session(
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_in_days=30,
        )

        jwt_token = self.session_service.generate_jwt_token(
            user_id=user.id,
            expires_in_minutes=60 * 24 * 7,  # 7 days
        )

        response.set_cookie(
            key="session_token",
            value=session.token,
            httponly=True,
            secure=settings.is_production,
            samesite="lax",
            max_age=60 * 60 * 24 * 30,  # 30 days
        )

        return AppResponse.ok(
            message="Login successful",
            data=AuthResponse(
                user=AuthUser(
                    id=user.id,
                    email=user.email,
                    email_verified=user.email_verified,
                ),
                session=AuthSession(
                    id=session.id,
                    expires_at=session.expires_at,
                ),
                access_token=jwt_token,  # For JWT-based auth
                token_type="bearer",
            ),
        )

    async def register(self, data: EmailRegister, request: Request, response: Response):
        if data.password != data.confirm_password:
            raise ValidationError("Passwords do not match")

        exists = await self.user_repository.exists(email=data.email)

        if exists:
            raise ValidationError(
                "Email already registered, please use a different email"
            )

        # Create user
        user = User(email=data.email, email_verified=False)
        user = await self.user_repository.create(user)

        # Create credential account with hashed password
        await self.account_service.create_credential_account(
            user_id=user.id, email=str(data.email), password=data.password
        )

        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        session = await self.session_service.create_session(
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_in_days=30,
        )

        jwt_token = self.session_service.generate_jwt_token(
            user_id=user.id,
            expires_in_minutes=60 * 24 * 7,  # 7 days
        )

        response.set_cookie(
            key="session_token",
            value=session.token,
            httponly=True,
            secure=settings.is_production,
            samesite="lax",
            max_age=60 * 60 * 24 * 30,  # 30 days
        )

        return AppResponse.created(
            message="User registered successfully",
            data=AuthResponse(
                user=AuthUser(
                    id=user.id,
                    email=user.email,
                    email_verified=user.email_verified,
                ),
                session=AuthSession(
                    id=session.id,
                    expires_at=session.expires_at,
                ),
                access_token=jwt_token,  # For JWT-based auth
                token_type="bearer",
            ),
        )

    async def logout(self):
        raise NoImplementationError("Logout not implemented yet")

    async def refresh_token(self):
        raise NoImplementationError("Refresh token not implemented yet")

    async def verify_email(self):
        raise NoImplementationError("Email verification not implemented yet")

    async def send_verification_email(self):
        raise NoImplementationError("Resend verification email not implemented yet")

    async def social_login(self):
        raise NoImplementationError("Social login not implemented yet")

    async def forgot_password(self):
        raise NoImplementationError("Password reset not implemented yet")

    async def reset_password(self):
        raise NoImplementationError("Change password not implemented yet")
