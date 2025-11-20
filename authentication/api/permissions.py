from ..core.database import Repository
from ..core.routing.routers.crud import AppCRUDRouter
from ..models import Permission
from ..schemas.permission import CreatePermission, UpdatePermission


async def exists_callback(
    permission: Permission, permission_repo: Repository[Permission]
):
    return await permission_repo.exists(
        resource=permission.resource, action=permission.action
    )


router = AppCRUDRouter(
    prefix="/permissions",
    model=Permission,
    create_schema=CreatePermission,
    update_schema=UpdatePermission,
    exists_callback=exists_callback,
    tags=["Permissions"],
)
