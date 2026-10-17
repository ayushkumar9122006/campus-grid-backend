from campus_grid.schema.base_schema import BaseSchema, MessageResponse, PaginatedResponse, PaginationQuery
from campus_grid.schema.user_schema import UserLogin, UserRegister, UserResponse, UserRoleUpdate
from campus_grid.schema.resource_schema import ResourceCreate, ResourceResponse, ResourceUpdate
from campus_grid.schema.booking_schema import BookingCreate, BookingResponse, BookingStatusUpdate
from campus_grid.schema.audit_log_schema import AuditLogCreate, AuditLogResponse
from campus_grid.schema.auth_schema import TokenResponse

__all__ = [
    "BaseSchema",
    "PaginationQuery",
    "PaginatedResponse",
    "MessageResponse",
    "UserRegister",
    "UserLogin",
    "UserResponse",
    "UserRoleUpdate",
    "ResourceCreate",
    "ResourceUpdate",
    "ResourceResponse",
    "BookingCreate",
    "BookingStatusUpdate",
    "BookingResponse",
    "AuditLogCreate",
    "AuditLogResponse",
    "TokenResponse",
]
