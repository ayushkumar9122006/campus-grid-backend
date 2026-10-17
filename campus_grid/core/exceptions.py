from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class DuplicatedError(HTTPException):
    def __init__(self, detail: Any = "Record already exists", headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(status.HTTP_409_CONFLICT, detail, headers)


class AuthError(HTTPException):
    def __init__(self, detail: Any = "Could not validate credentials", headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail, headers)


class PermissionDeniedError(HTTPException):
    def __init__(self, detail: Any = "Permission denied for this operation", headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(status.HTTP_403_FORBIDDEN, detail, headers)


class NotFoundError(HTTPException):
    def __init__(self, detail: Any = "Resource not found", headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, detail, headers)


class ValidationError(HTTPException):
    def __init__(self, detail: Any = "Validation error", headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, detail, headers)


class BookingConflictError(HTTPException):
    def __init__(self, detail: Any = "Slot conflict: Resource is fully booked for the requested time interval", headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(status.HTTP_409_CONFLICT, detail, headers)


class ResourceUnavailableError(HTTPException):
    def __init__(self, detail: Any = "Requested resource is currently not available for reservation", headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(status.HTTP_400_BAD_REQUEST, detail, headers)


class InvalidTimeRangeError(HTTPException):
    def __init__(self, detail: Any = "Invalid booking time range: end_time must be after start_time", headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(status.HTTP_400_BAD_REQUEST, detail, headers)
