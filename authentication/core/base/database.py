import datetime
from uuid import UUID, uuid4

import arrow
import sqlalchemy as sa
from sqlmodel import SQLModel, Field

from .app import AppObject


def get_current_utc_datetime() -> datetime.datetime:
    """
    Get the current UTC datetime with timezone awareness
    """
    return arrow.utcnow().datetime


class DatabaseObject(AppObject, SQLModel):
    """
    Base database object class
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    created_at: datetime.datetime = Field(
        default_factory=get_current_utc_datetime,
        sa_column=sa.Column(
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False
        )
    )
    updated_at: datetime.datetime = Field(
        default_factory=get_current_utc_datetime,
        sa_column=sa.Column(
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=get_current_utc_datetime,
            nullable=False
        )
    )
