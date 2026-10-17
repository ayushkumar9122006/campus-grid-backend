from datetime import datetime
from typing import Optional
from pydantic import Field, field_validator, model_validator

from campus_grid.model.resource import ResourceCategory, ResourceStatus
from campus_grid.schema.base_schema import BaseSchema


class ResourceCreate(BaseSchema):
    name: str = Field(..., min_length=2, max_length=255, description="Resource display name")
    category: str = Field(..., description="Category, e.g. lab_equipment, media_gear, facility")
    total_quantity: int = Field(default=1, ge=1, description="Total units available across campus")
    available_quantity: Optional[int] = Field(default=None, ge=0, description="Available unreserved units")
    status: str = Field(default=ResourceStatus.AVAILABLE.value, description="Status: available, maintenance, retired")

    @field_validator("name")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Name cannot be empty or purely whitespace")
        return clean

    @model_validator(mode="after")
    def sync_quantities(self) -> "ResourceCreate":
        if self.available_quantity is None:
            self.available_quantity = self.total_quantity
        elif self.available_quantity > self.total_quantity:
            raise ValueError("available_quantity cannot exceed total_quantity")
        return self


class ResourceUpdate(BaseSchema):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    category: Optional[str] = None
    total_quantity: Optional[int] = Field(default=None, ge=1)
    available_quantity: Optional[int] = Field(default=None, ge=0)
    status: Optional[str] = None

    @model_validator(mode="after")
    def validate_quantities(self) -> "ResourceUpdate":
        if self.total_quantity is not None and self.available_quantity is not None:
            if self.available_quantity > self.total_quantity:
                raise ValueError("available_quantity cannot exceed total_quantity")
        return self


class ResourceResponse(BaseSchema):
    id: int
    name: str
    category: str
    total_quantity: int
    available_quantity: int
    status: str
    created_at: datetime
    updated_at: datetime
