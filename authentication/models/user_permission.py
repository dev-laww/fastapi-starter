from enum import Enum
from uuid import UUID

from sqlalchemy import UniqueConstraint, Column, Enum as SQLEnum
from sqlmodel import Field

from ..core.base import BaseDBModel


class GrantType(Enum):
    GRANT = "grant"
    DENY = "deny"
    INHERIT = "inherit"


class UserPermission(BaseDBModel, table=True):
    __tablename__ = "user_permissions"
    __table_args__ = (UniqueConstraint("user_id", "permission_id"),)

    user_id: UUID = Field(foreign_key="users.id", index=True)
    permission_id: UUID = Field(foreign_key="permissions.id", index=True)
    grant_type: GrantType = Field(
        sa_column=Column(SQLEnum(GrantType, name="grant_type")),
        default=GrantType.INHERIT,
    )
