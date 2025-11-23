import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Column, DateTime
from sqlmodel import Field, Relationship

from ..core.base import BaseDBModel

if TYPE_CHECKING:
    from .user import User


class Session(BaseDBModel, table=True):
    __tablename__ = "sessions"

    user_id: UUID = Field(foreign_key="users.id", index=True)
    token: str
    expires_at: datetime.datetime = Field(sa_column=Column(DateTime(timezone=True)))
    ip_address: Optional[str]
    user_agent: Optional[str]

    user: "User" = Relationship(
        back_populates="sessions", sa_relationship_kwargs={"lazy": "selectin"}
    )

    @property
    def is_expired(self) -> bool:
        return datetime.datetime.utcnow() > self.expires_at
