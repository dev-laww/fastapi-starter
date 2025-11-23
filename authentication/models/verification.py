import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

import arrow
from sqlalchemy import DateTime
from sqlmodel import Field, Column, Relationship

from ..core.base import BaseDBModel

if TYPE_CHECKING:
    from .user import User


class VerificationIdentifier(Enum):
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"
    TWO_FACTOR_AUTH = "two_factor_auth"


class Verification(BaseDBModel, table=True):
    __tablename__ = "verifications"

    identifier: str
    user_id: UUID = Field(foreign_key="users.id", index=True)
    value: str
    expires_at: datetime.datetime = Field(sa_column=Column(DateTime(timezone=True)))

    user: "User" = Relationship(
        back_populates="verifications", sa_relationship_kwargs={"lazy": "selectin"}
    )

    @property
    def is_expired(self) -> bool:
        return arrow.utcnow().datetime > self.expires_at
