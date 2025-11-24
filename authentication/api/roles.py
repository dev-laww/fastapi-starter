from typing import Annotated
from uuid import UUID

from fastapi.params import Depends

from ..controllers.role import RoleController
from ..core.routing import post, get, delete
from ..core.routing.routers import AppCRUDRouter
from ..models import Role
from ..schemas.role import UpdateRole, CreateRole


async def exists_callback(role: Role, role_repo):
    return await role_repo.exists(name=role.name)


class RolesRouter(AppCRUDRouter[Role]):
    controller: Annotated[RoleController, Depends()]

    def __init__(self):
        super().__init__(
            prefix="/roles",
            model=Role,
            create_schema=CreateRole,
            update_schema=UpdateRole,
            exists_callback=exists_callback,
            tags=["Roles"],
        )

    @get("/{id}/permissions")
    async def get_permissions(self, id: UUID):
        return await self.controller.get_role_permissions(id)

    @post("/{id}/permissions/{permission_id}")
    async def assign_permission(self, id: UUID, permission_id: UUID):
        return await self.controller.assign_permissions_to_role(id, permission_id)

    @delete("/{id}/permissions/{permission_id}")
    async def remove_permission(self, id: UUID, permission_id: UUID):
        return await self.controller.remove_permissions_from_role(id, permission_id)


router = RolesRouter()
