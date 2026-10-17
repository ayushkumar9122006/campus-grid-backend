from datetime import datetime, timezone
from typing import Optional
from pydantic import Field, model_validator

from campus_grid.model.booking import BookingStatus
from campus_grid.schema.base_schema import BaseSchema


class BookingCreate(BaseSchema):
    resource_id: int = Field(..., ge=1, description="Target resource ID")
    start_time: datetime = Field(..., description="Reservation start timestamp (ISO-8601)")
    end_time: datetime = Field(..., description="Reservation end timestamp (ISO-8601)")

    @model_validator(mode="after")
    def validate_slot_interval(self) -> "BookingCreate":
        start = self.start_time
        end = self.end_time

        # Ensure datetime comparison works regardless of timezone attachment
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)

        if end <= start:
            raise ValueError("end_time must be strictly after start_time")

        duration = (end - start).total_seconds()
        if duration < 300:  # Minimum 5 minutes
            raise ValueError("Booking duration must be at least 5 minutes")

        if duration > 86400 * 30:  # Max 30 days
            raise ValueError("Booking duration cannot exceed 30 days")

        return self


class BookingStatusUpdate(BaseSchema):
    status: BookingStatus = Field(..., description="Target status: pending, approved, returned, cancelled")


class BookingResponse(BaseSchema):
    id: int
    user_id: int
    resource_id: int
    start_time: datetime
    end_time: datetime
    status: BookingStatus
    created_at: datetime
    updated_at: datetime
    resource_name: Optional[str] = None
    user_email: Optional[str] = None
