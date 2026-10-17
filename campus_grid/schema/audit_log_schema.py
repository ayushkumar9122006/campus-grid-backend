from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import Field

from campus_grid.schema.base_schema import BaseSchema


class AuditLogCreate(BaseSchema):
    user_id: Optional[int] = Field(default=None, description="Actor user ID")
    action: str = Field(..., description="Action tag, e.g. BOOKING_CREATE, RESOURCE_UPDATE")
    meta_data: Optional[Dict[str, Any]] = Field(default=None, description="Structured contextual event metadata")


class AuditLogResponse(BaseSchema):
    id: int
    user_id: Optional[int]
    action: str
    timestamp: datetime
    meta_data: Optional[Dict[str, Any]]
