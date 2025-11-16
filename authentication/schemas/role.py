from typing import Optional

from pydantic import model_validator

from ..core.base import BaseModel


class CreateRole(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True


# TODO: Create a update schema factory that enforces at least one field to be set
class UpdateRole(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

    @model_validator(mode="after")
    def at_least_one_field(self):
        if not any(
            value is not None for value in self.model_dump(exclude_unset=True).values()
        ):
            raise ValueError("At least one field must be provided for update")

        return self
