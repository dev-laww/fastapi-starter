from typing import TypeVar, List, Optional

from pydantic import Field

from ..core.base import BaseModel

T = TypeVar("T", bound=BaseModel)


class PaginationParams(BaseModel):
    """
    Common pagination parameters for API requests.
    """

    page: int = Field(default=1)
    limit: int = Field(default=10, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class PaginationInfo(BaseModel):
    """
    Common pagination information for API responses.
    """

    total_items: int
    total_pages: int
    current_page: int
    items_per_page: int
    has_next: bool
    has_previous: bool
    next_page_url: Optional[str] = None
    previous_page_url: Optional[str] = None


class PaginatedResponse[T](BaseModel):
    """
    Common paginated response schema.
    """

    items: List[T]
    pagination: PaginationInfo
