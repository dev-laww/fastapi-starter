import datetime
import secrets
from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends
from jose import jwt, JWTError

from ..core.base import AppObject
from ..core.config import get_settings
from ..core.database import Repository
from ..core.database.filters import lt
from ..core.database.repository import get_repository
from ..core.exceptions import AppException
from ..core.utils import get_current_utc_datetime
from ..models import Session
from ..schemas.auth import JWTPayload

settings = get_settings()


class SessionService(AppObject):
    """
    Service for managing user sessions with support for both cookie-based and JWT-based authentication.

    Similar to better-auth's session management:
    - Cookie-based: Creates a session record in DB with a secure token, stored in HTTP-only cookie
    - JWT-based: Generates JWT tokens that can be used in Authorization headers
    """

    def __init__(
        self,
        session_repository: Annotated[
            Repository[Session], Depends(get_repository(Session))
        ],
    ):
        self.session_repository = session_repository

    def generate_session_token(self) -> str:
        """
        Generate a secure random token for session storage.
        Similar to better-auth's session token generation.
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_jwt_token(
        user_id: UUID,
        expires_in_minutes: int = 60 * 24 * 7,  # Default 7 days
        additional_claims: Optional[dict] = None,
    ) -> str:
        """
        Generate a JWT token for the user.
        Can be used in Authorization: Bearer <token> headers.
        """
        now = get_current_utc_datetime()
        expire = now + datetime.timedelta(minutes=expires_in_minutes)

        payload = JWTPayload(
            sub=str(user_id),
            iat=int(now.timestamp()),
            exp=int(expire.timestamp()),
            type="access",
        )

        if additional_claims:
            payload.update(additional_claims)

        token = jwt.encode(
            payload.model_dump(), settings.app.jwt_secret, algorithm="HS256"
        )

        return token

    @staticmethod
    def verify_jwt_token(token: str) -> Optional[JWTPayload]:
        """
        Verify and decode a JWT token.
        Returns the payload if valid, None otherwise.
        """
        try:
            payload = jwt.decode(token, settings.app.jwt_secret, algorithms=["HS256"])
            return JWTPayload.model_validate(payload)
        except JWTError:
            return None

    async def create_session(
        self,
        user_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        expires_in_days: int = 30,
    ) -> Session:
        """
        Create a new session record in the database.
        This is used for cookie-based authentication.
        Similar to better-auth's session creation.
        """
        token = self.generate_session_token()
        expires_at = get_current_utc_datetime() + datetime.timedelta(
            days=expires_in_days
        )

        session = Session(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return await self.session_repository.create(session)

    async def get_session_by_token(self, token: str) -> Optional[Session]:
        """
        Retrieve a session by its token.
        Used for cookie-based authentication validation.
        """
        session = await self.session_repository.get_first(token=token)
        if not session:
            return None

        # Check if session is expired
        if session.is_expired:
            await self.session_repository.delete(session.id)
            return None

        return session

    async def get_session_by_id(self, session_id: UUID) -> Optional[Session]:
        """Retrieve a session by its ID."""
        return await self.session_repository.get(session_id)

    async def delete_session(self, session_id: UUID) -> None:
        """Delete a session by its ID."""
        await self.session_repository.delete(session_id)

    async def delete_user_sessions(self, user_id: UUID) -> None:
        """Delete all sessions for a user."""
        sessions = await self.session_repository.all(user_id=user_id)
        for session in sessions:
            await self.session_repository.delete(session.id)

    async def refresh_session(
        self, session_id: UUID, expires_in_days: int = 30
    ) -> Session:
        """
        Refresh a session by extending its expiration time.
        """
        session = await self.session_repository.get_or_raise(session_id)

        if session.expires_at < get_current_utc_datetime():
            raise AppException("Cannot refresh an expired session")

        new_expires_at = get_current_utc_datetime() + datetime.timedelta(
            days=expires_in_days
        )

        return await self.session_repository.update(
            session_id, expires_at=new_expires_at
        )

    async def cleanup_expired_sessions(self) -> int:
        """
        Delete all expired sessions.
        Returns the number of sessions deleted.
        """
        now = get_current_utc_datetime()

        expired_sessions = await self.session_repository.all(expires_at=lt(now))
        count = 0

        for session in expired_sessions:
            await self.session_repository.delete(session.id)
            count += 1

        return count
