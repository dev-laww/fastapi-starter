from enum import Enum
from typing import Optional, TYPE_CHECKING, List

import sqlalchemy as sa
from sqlmodel import Field, Relationship

from .role_permission import RolePermission
from ..core.base import BaseDBModel

if TYPE_CHECKING:
    from .role import Role


class Action(Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    UPDATE = "update"


class Permission(BaseDBModel, table=True):
    __tablename__ = "permissions"
    __table_args__ = (sa.UniqueConstraint("resource", "action"),)

    resource: str = Field(index=True)
    action: Action = Field(
        sa_column=sa.Column(sa.Enum(Action), nullable=False, index=True)
    )
    description: Optional[str] = Field(default=None)

    roles: List["Role"] = Relationship(
        back_populates="permissions",
        link_model=RolePermission,
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    @property
    def name(self):
        return f"{self.action.value}:{self.resource}"
