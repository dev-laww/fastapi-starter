from typing import Optional


from ..core.base import BaseModel
from ..models.permission import Action


class CreatePermission(BaseModel):
    resource: str
    action: Action
    description: Optional[str] = None


UpdatePermission = CreatePermission.make_fields_optional("UpdatePermission")
