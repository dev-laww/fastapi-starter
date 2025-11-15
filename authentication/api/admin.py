from typing import Annotated
from uuid import UUID

from fastapi import Depends, APIRouter

from ..controllers.admin import AdminController
from ..core.routing import AppRouter, get, post, delete
from ..schemas import Role
from ..schemas.common import PaginationParams


class AdminRouter(AppRouter):
    controller: Annotated[AdminController, Depends()]

    @get("/roles")
    async def get_roles(self, pagination: PaginationParams = Depends()):
        return await self.controller.get_roles(pagination)

    @post("/roles")
    async def create_role(self, role: Role):
        return await self.controller.create_role(role)

    @get("/roles/{role_id}")
    async def get_role(self, role_id: UUID):
        return await self.controller.get_role(role_id)

    @delete("/roles/{role_id}")
    async def soft_delete_role(self, role_id: UUID):
        return await self.controller.soft_delete_role(role_id)

    @delete("/roles/{role_id}/force")
    async def delete_role(self, role_id: UUID):
        return await self.controller.delete_role(role_id)


test_router = APIRouter(prefix="/test", tags=["Test"])


@test_router.get("/roles")
def test_get_roles():
    return {"message": "This is a test endpoint for roles."}


@test_router.post("/roles")
def test_create_role():
    return {"message": "This is a test endpoint for creating a role."}


router = AdminRouter(prefix="/admin", tags=["Admin"])
