from uuid import UUID

from ..core.exceptions import NoImplementationError
from ..core.routing import post, get, delete
from ..core.routing.routers import AppCRUDRouter
from ..models import User


class UsersRouter(AppCRUDRouter[User]):
    def __init__(self):
        super().__init__(
            prefix="/users",
            model=User,
            include_create=False,
            include_delete=False,
            include_update=False,
            tags=["Users"],
        )

    @get("/{id}/roles")
    def get_roles(self, id: UUID):
        raise NoImplementationError("Get user roles not implemented")

    @post("/{id}/roles/{role_id}")
    def add_role(self, id: UUID, role_id: UUID):
        raise NoImplementationError("Add role to user not implemented")

    @delete("/{id}/roles/{role_id}")
    def remove_role(self, id: UUID, role_id: UUID):
        raise NoImplementationError("Remove role from user not implemented")


router = UsersRouter()
