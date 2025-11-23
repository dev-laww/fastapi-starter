import secrets
from typing import Annotated, Dict, Any, Tuple
from uuid import UUID

import arrow
from fastapi import Depends, Request
from starlette.responses import Response, RedirectResponse

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
from ..models import User, Verification
from ..models.verification import VerificationIdentifier
from ..schemas.auth import (
    EmailLogin,
    EmailRegister,
    AuthResponse,
    AuthUser,
    AuthSession,
    ResetPassword,
    VerifyEmail,
    EmailWithCallback,
)
from ..services import AccountService, SessionService
from ..services.email import EmailService


class AuthController(Controller):
    SESSION_EXPIRES_DAYS = 30
    JWT_EXPIRES_DAYS = 7
    EMAIL_VERIFICATION_EXPIRES_HOURS = 1
    PASSWORD_RESET_EXPIRES_MINUTES = 30
    SITE_NAME = "MyApp"
    IMAGE_URL = "https://cdn.brandfetch.io/idDpCfN4VD/w/400/h/400/theme/dark/icon.png?c=1bxid64Mup7aczewSAYMX&t=1759982772575"
    BASE_URL = "https://myapp.example.com"

    def __init__(
        self,
        user_repository: Annotated[Repository[User], Depends(get_repository(User))],
        account_service: Annotated[AccountService, Depends()],
        session_service: Annotated[SessionService, Depends()],
        email_service: Annotated[EmailService, Depends()],
        verification_repository: Annotated[
            Repository[Verification], Depends(get_repository(Verification))
        ],
    ):
        self.user_repository = user_repository
        self.account_service = account_service
        self.session_service = session_service
        self.verification_repository = verification_repository
        self.email_service = email_service

    async def login(self, data: EmailLogin, request: Request, response: Response):
        account = await self.account_service.verify_credential(
            email=str(data.email), password=data.password
        )

        if not account:
            raise AuthenticationError("Invalid email or password")

        user = await self.user_repository.get_or_raise(account.user_id)
        session, jwt_token = await self._create_session_and_token(user.id, request)
        self._set_session_cookie(response, session.token)

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
                access_token=jwt_token,
                token_type="bearer",
            ),
        )

    async def register(self, data: EmailRegister, request: Request, response: Response):
        if await self.user_repository.exists(email=data.email):
            raise ValidationError(
                "Email already registered, please use a different email"
            )

        user = User(email=data.email, email_verified=False)
        user = await self.user_repository.create(user)

        await self.account_service.create_credential_account(
            user_id=user.id, email=str(data.email), password=data.password
        )

        session, jwt_token = await self._create_session_and_token(user.id, request)
        self._set_session_cookie(response, session.token)

        context = {
            **self._get_base_email_context(),
            "user_name": user.email,
            "welcome_url": f"{self.BASE_URL}/dashboard",
        }
        html = self.email_service.render_template("onboarding.html", context)
        self.email_service.send_email(
            to_email=str(user.email),
            subject="Welcome to MyApp!",
            html_content=html,
        )

        if data.send_verification_email:
            verification = self._create_verification_token(
                user.id,
                VerificationIdentifier.EMAIL_VERIFICATION.value,
                expires_hours=self.EMAIL_VERIFICATION_EXPIRES_HOURS,
            )
            await self.verification_repository.create(verification)

            context = {
                **self._get_base_email_context(),
                "verification_url": f"{self.BASE_URL}/verify-email?token={verification.value}",
            }

            html = self.email_service.render_template(
                "email-verification.html", context
            )
            self.email_service.send_email(
                to_email=str(user.email),
                subject="Verify your email address",
                html_content=html,
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
                access_token=jwt_token,
                token_type="bearer",
            ),
        )

    async def logout(self):
        raise NoImplementationError("Logout not implemented yet")

    async def refresh_token(self):
        raise NoImplementationError("Refresh token not implemented yet")

    async def verify_email(self, data: VerifyEmail):
        verification = await self.verification_repository.get_first(
            value=data.token, identifier=VerificationIdentifier.EMAIL_VERIFICATION.value
        )

        if not verification:
            raise ValidationError("Invalid or expired verification token")

        if verification.is_expired:
            raise ValidationError("Verification token has expired")

        user = await self.user_repository.get_or_raise(verification.user_id)

        if user.email_verified:
            if data.callback_url:
                return RedirectResponse(url=data.callback_url)
            return AppResponse.ok(
                message="Email is already verified", data={"email_verified": True}
            )

        user = await self.user_repository.update(user.id, email_verified=True)
        await self.verification_repository.delete(verification.id)

        context = {
            **self._get_base_email_context(),
            "user_name": user.email,
            "dashboard_url": data.callback_url or f"{self.BASE_URL}/dashboard",
        }
        html = self.email_service.render_template("verification-success.html", context)

        self.email_service.send_email(
            to_email=str(user.email),
            subject="Email verified successfully",
            html_content=html,
        )

        if data.callback_url:
            return RedirectResponse(url=data.callback_url)

        return AppResponse.ok(
            message="Email verified successfully",
            data={
                "email_verified": True,
                "user_id": str(user.id),
                "email": str(user.email),
            },
        )

    async def send_verification_email(self, data: EmailWithCallback):
        user = await self.user_repository.get_first(email=data.email)

        if not user:
            raise ValidationError("Email not registered")

        if user.email_verified:
            raise ValidationError("Email is already verified")

        verification = self._create_verification_token(
            user.id,
            VerificationIdentifier.EMAIL_VERIFICATION.value,
            expires_hours=self.EMAIL_VERIFICATION_EXPIRES_HOURS,
        )
        await self.verification_repository.create(verification)

        verification_url = (
            f"{data.callback_url}?token={verification.value}"
            if data.callback_url
            else None
        )

        context = {
            **self._get_base_email_context(),
            "verification_url": verification_url,
            "user_name": user.email,
            "expiration_hours": self.EMAIL_VERIFICATION_EXPIRES_HOURS,
        }
        html = self.email_service.render_template("email-verification.html", context)
        self.email_service.send_email(
            to_email=str(user.email),
            subject="Verify your email address",
            html_content=html,
        )

        return AppResponse.ok(
            message="Verification email sent successfully",
            data={"token": verification.value},
        )

    async def social_login(self):
        raise NoImplementationError("Social login not implemented yet")

    async def forgot_password(self, data: EmailWithCallback):
        user = await self.user_repository.get_first(email=data.email)

        if not user:
            raise ValidationError("Email not registered")

        verification = self._create_verification_token(
            user.id,
            VerificationIdentifier.PASSWORD_RESET.value,
            expires_minutes=self.PASSWORD_RESET_EXPIRES_MINUTES,
        )
        await self.verification_repository.create(verification)

        reset_url = (
            f"{data.callback_url}?token={verification.value}"
            if data.callback_url
            else f"{self.BASE_URL}/reset-password?token={verification.value}"
        )

        context = {
            **self._get_base_email_context(),
            "expiration_minutes": self.PASSWORD_RESET_EXPIRES_MINUTES,
            "reset_url": reset_url,
        }
        html = self.email_service.render_template("forgot-password.html", context)
        self.email_service.send_email(
            to_email=str(user.email),
            subject="Reset your password",
            html_content=html,
        )

        return AppResponse.ok(
            message="A password reset link has been sent",
            data={"token": verification.value},
        )

    async def reset_password(self, data: ResetPassword):
        verification = await self.verification_repository.get_first(
            value=data.token, identifier=VerificationIdentifier.PASSWORD_RESET.value
        )

        if not verification:
            raise ValidationError("Invalid or expired password reset token")

        if verification.is_expired:
            raise ValidationError("Password reset token has expired")

        user = await self.user_repository.get_or_raise(verification.user_id)

        account = await self.account_service.get_account_by_email(str(user.email))

        if not account:
            raise ValidationError("Password not set for this account")

        await self.account_service.update_account_password(
            account_id=account.id, new_password=data.password
        )
        await self.verification_repository.delete(verification.id)

        context = {
            **self._get_base_email_context(),
            "login_url": f"{self.BASE_URL}/login",
        }
        html = self.email_service.render_template("reset-password.html", context)
        self.email_service.send_email(
            to_email=str(user.email),
            subject="Password reset successful",
            html_content=html,
        )

        return AppResponse.ok(message="Password reset successfully")

    async def _create_session_and_token(
        self, user_id: UUID, request: Request
    ) -> Tuple[Any, str]:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        session = await self.session_service.create_session(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_in_days=self.SESSION_EXPIRES_DAYS,
        )
        jwt_token = self.session_service.generate_jwt_token(
            user_id=user_id,
            expires_in_minutes=60 * 24 * self.JWT_EXPIRES_DAYS,
        )
        return session, jwt_token

    def _set_session_cookie(self, response: Response, session_token: str):
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=settings.is_production,
            samesite="lax",
            max_age=60 * 60 * 24 * self.SESSION_EXPIRES_DAYS,
        )

    def _get_base_email_context(self) -> Dict[str, str]:
        return {
            "site_name": self.SITE_NAME,
            "image_url": self.IMAGE_URL,
            "base_url": self.BASE_URL,
        }

    @staticmethod
    def _create_verification_token(
        user_id: UUID,
        identifier: str,
        expires_hours: int | None = None,
        expires_minutes: int | None = None,
    ) -> Verification:
        expires_at = arrow.utcnow()

        if expires_hours:
            expires_at = expires_at.shift(hours=+expires_hours)
        elif expires_minutes:
            expires_at = expires_at.shift(minutes=+expires_minutes)

        return Verification(
            user_id=user_id,
            identifier=identifier,
            value=secrets.token_urlsafe(32),
            expires_at=expires_at.datetime,
        )
