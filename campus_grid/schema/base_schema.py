from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


class PaginationQuery(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number starting from 1")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page (max 100)")
    ordering: Optional[str] = Field(default="-id", description="Field to sort by, prefix with '-' for desc")


class PaginatedResponse(BaseSchema, Generic[T]):
    items: List[T]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class MessageResponse(BaseSchema):
    message: str
    detail: Optional[str] = None
