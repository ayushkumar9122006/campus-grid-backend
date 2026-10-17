from typing import Optional
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, status

from campus_grid.core.container import Container
from campus_grid.core.dependencies import get_current_active_user, require_faculty_or_admin
from campus_grid.model.booking import BookingStatus
from campus_grid.model.user import User
from campus_grid.schema.base_schema import PaginatedResponse
from campus_grid.schema.booking_schema import BookingCreate, BookingResponse
from campus_grid.services.booking_service import BookingService

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
@inject
def create_booking(
    booking_in: BookingCreate,
    service: BookingService = Depends(Provide[Container.booking_service]),
    current_user: User = Depends(get_current_active_user),
):
    """
    Reserve a campus resource.
    - Transactional double-booking prevention engine verifies slot availability and quantity limits.
    - Students create bookings in 'pending' status.
    - Faculty and Admin bookings are automatically 'approved'.
    """
    booking = service.create_booking(booking_in, current_user=current_user)
    return booking


@router.get("", response_model=PaginatedResponse[BookingResponse])
@inject
def list_bookings(
    status: Optional[BookingStatus] = Query(default=None, description="Filter by status"),
    resource_id: Optional[int] = Query(default=None, description="Filter by resource ID"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: BookingService = Depends(Provide[Container.booking_service]),
    current_user: User = Depends(get_current_active_user),
):
    """
    List bookings.
    - Students are strictly restricted to viewing only their own bookings.
    - Faculty and Admins can view all reservations across campus.
    """
    return service.list_bookings(
        current_user=current_user,
        status=status,
        resource_id=resource_id,
        page=page,
        page_size=page_size,
    )


@router.get("/my", response_model=PaginatedResponse[BookingResponse])
@inject
def get_my_bookings(
    status: Optional[BookingStatus] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: BookingService = Depends(Provide[Container.booking_service]),
    current_user: User = Depends(get_current_active_user),
):
    """Convenience endpoint to retrieve reservations belonging to the authenticated user."""
    return service.list_bookings(
        current_user=current_user,
        status=status,
        page=page,
        page_size=page_size,
    )


@router.get("/{booking_id}", response_model=BookingResponse)
@inject
def get_booking(
    booking_id: int,
    service: BookingService = Depends(Provide[Container.booking_service]),
    current_user: User = Depends(get_current_active_user),
):
    """Get single booking details. Students can only inspect their own bookings."""
    return service.get_booking_by_id(booking_id, current_user=current_user)


@router.post("/{booking_id}/approve", response_model=BookingResponse)
@inject
def approve_booking(
    booking_id: int,
    service: BookingService = Depends(Provide[Container.booking_service]),
    current_user: User = Depends(require_faculty_or_admin),
):
    """Approve a pending booking request (Faculty & Admin only)."""
    return service.approve_booking(booking_id, approver=current_user)


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
@inject
def cancel_booking(
    booking_id: int,
    service: BookingService = Depends(Provide[Container.booking_service]),
    current_user: User = Depends(get_current_active_user),
):
    """Cancel a booking. Students can cancel their own; Faculty/Admin can cancel any."""
    return service.cancel_booking(booking_id, actor=current_user)


@router.post("/{booking_id}/return", response_model=BookingResponse)
@inject
def return_booking(
    booking_id: int,
    service: BookingService = Depends(Provide[Container.booking_service]),
    current_user: User = Depends(get_current_active_user),
):
    """Mark an approved reservation as returned upon equipment check-in."""
    return service.return_booking(booking_id, actor=current_user)
