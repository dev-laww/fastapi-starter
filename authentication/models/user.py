from typing import Optional, TYPE_CHECKING, List

from pydantic import EmailStr
from sqlmodel import Field, Relationship

from .user_role import UserRole
from ..core.base import BaseDBModel

if TYPE_CHECKING:
    from .role import Role
    from .account import Account
    from .session import Session
    from .verification import Verification


class User(BaseDBModel, table=True):
    __tablename__ = "users"

    email: EmailStr = Field(unique=True, index=True)
    email_verified: bool = Field(default=False)
    image: Optional[str] = Field(default=None)

    roles: List["Role"] = Relationship(
        back_populates="users",
        link_model=UserRole,
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    accounts: List["Account"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}
    )

    sessions: List["Session"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}
    )

    verifications: List["Verification"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}
    )
