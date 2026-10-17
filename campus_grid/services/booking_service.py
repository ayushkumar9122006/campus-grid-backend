import math
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from contextlib import AbstractContextManager

from sqlalchemy.orm import Session

from campus_grid.core.exceptions import (
    BookingConflictError,
    NotFoundError,
    PermissionDeniedError,
    ResourceUnavailableError,
    ValidationError,
)
from campus_grid.model.booking import Booking, BookingStatus
from campus_grid.model.resource import Resource, ResourceStatus
from campus_grid.model.user import User, UserRole
from campus_grid.repository.audit_log_repository import AuditLogRepository
from campus_grid.repository.booking_repository import BookingRepository
from campus_grid.repository.resource_repository import ResourceRepository
from campus_grid.schema.booking_schema import BookingCreate
from campus_grid.services.base_service import BaseService


class BookingService(BaseService[Booking]):
    def __init__(
        self,
        booking_repository: BookingRepository,
        resource_repository: ResourceRepository,
        audit_log_repository: AuditLogRepository,
        session_factory: Callable[..., AbstractContextManager[Session]],
    ):
        super().__init__(booking_repository)
        self.booking_repository = booking_repository
        self.resource_repository = resource_repository
        self.audit_log_repository = audit_log_repository
        self.session_factory = session_factory

    def create_booking(self, booking_in: BookingCreate, current_user: User) -> Booking:
        """
        Transactional double-booking prevention engine:
        1. Opens an atomic database transaction.
        2. Acquires row-level pessimistic lock on the target Resource.
        3. Verifies resource operational status.
        4. Calculates concurrent overlapping reservations during the interval [start_time, end_time].
        5. Rejects with BookingConflictError (409) if active bookings meet or exceed total units.
        6. Persists the reservation and records an immutable AuditLog within the same transaction.
        """
        with self.session_factory() as session:
            # 1. Pessimistic lock on resource row
            resource = self.resource_repository.get_by_id_locked(session, booking_in.resource_id)
            if not resource:
                raise NotFoundError(detail=f"Resource with ID {booking_in.resource_id} not found")

            # 2. Check operational status
            if resource.status != ResourceStatus.AVAILABLE.value:
                raise ResourceUnavailableError(
                    detail=f"Resource '{resource.name}' is currently '{resource.status}' and unavailable for reservations"
                )

            # 3. Transactional overlap query
            active_overlaps = self.booking_repository.count_overlapping_bookings(
                session=session,
                resource_id=resource.id,
                start_time=booking_in.start_time,
                end_time=booking_in.end_time,
            )

            # 4. Capacity and double-booking verification
            if active_overlaps >= resource.total_quantity:
                raise BookingConflictError(
                    detail=(
                        f"Double-booking prevented: Resource '{resource.name}' has reached its full capacity "
                        f"({active_overlaps}/{resource.total_quantity} reserved) for the selected interval "
                        f"{booking_in.start_time.isoformat()} to {booking_in.end_time.isoformat()}."
                    )
                )

            # 5. Role-based initial status: Faculty & Admins auto-approved, Students start as pending
            if current_user.role in [UserRole.FACULTY, UserRole.ADMIN]:
                initial_status = BookingStatus.APPROVED
            else:
                initial_status = BookingStatus.PENDING

            booking = Booking(
                user_id=current_user.id,
                resource_id=resource.id,
                start_time=booking_in.start_time,
                end_time=booking_in.end_time,
                status=initial_status,
            )
            session.add(booking)
            session.flush()

            # 6. Audit logging within the same transaction
            self.audit_log_repository.log(
                session=session,
                user_id=current_user.id,
                action="BOOKING_CREATE",
                meta_data={
                    "booking_id": booking.id,
                    "resource_id": resource.id,
                    "resource_name": resource.name,
                    "start_time": booking.start_time.isoformat(),
                    "end_time": booking.end_time.isoformat(),
                    "status": booking.status.value,
                },
            )

            session.commit()
            session.refresh(booking)
            return booking

    def approve_booking(self, booking_id: int, approver: User) -> Booking:
        """Approve a pending booking with slot capacity re-verification."""
        with self.session_factory() as session:
            booking = session.get(Booking, booking_id)
            if not booking:
                raise NotFoundError(detail=f"Booking with ID {booking_id} not found")

            if booking.status != BookingStatus.PENDING:
                raise ValidationError(detail=f"Cannot approve booking in '{booking.status.value}' status")

            # Lock resource & re-verify slot availability
            resource = self.resource_repository.get_by_id_locked(session, booking.resource_id)
            if not resource:
                raise NotFoundError(detail=f"Associated resource {booking.resource_id} not found")

            other_overlaps = self.booking_repository.count_overlapping_bookings(
                session=session,
                resource_id=booking.resource_id,
                start_time=booking.start_time,
                end_time=booking.end_time,
                exclude_booking_id=booking.id,
            )

            if other_overlaps >= resource.total_quantity:
                raise BookingConflictError(
                    detail="Cannot approve booking: resource slot is now occupied by another approved reservation"
                )

            booking.status = BookingStatus.APPROVED
            self.audit_log_repository.log(
                session=session,
                user_id=approver.id,
                action="BOOKING_APPROVE",
                meta_data={"booking_id": booking.id, "approver_id": approver.id},
            )

            session.commit()
            session.refresh(booking)
            return booking

    def cancel_booking(self, booking_id: int, actor: User) -> Booking:
        """Cancel a booking. Students can cancel their own; Faculty/Admin can cancel any."""
        with self.session_factory() as session:
            booking = session.get(Booking, booking_id)
            if not booking:
                raise NotFoundError(detail=f"Booking with ID {booking_id} not found")

            if actor.role == UserRole.STUDENT and booking.user_id != actor.id:
                raise PermissionDeniedError(detail="Students are only authorized to cancel their own bookings")

            if booking.status in [BookingStatus.CANCELLED, BookingStatus.RETURNED]:
                raise ValidationError(detail=f"Booking is already finalized with status '{booking.status.value}'")

            booking.status = BookingStatus.CANCELLED
            self.audit_log_repository.log(
                session=session,
                user_id=actor.id,
                action="BOOKING_CANCEL",
                meta_data={"booking_id": booking.id, "cancelled_by": actor.id},
            )

            session.commit()
            session.refresh(booking)
            return booking

    def return_booking(self, booking_id: int, actor: User) -> Booking:
        """Mark an approved booking as returned."""
        with self.session_factory() as session:
            booking = session.get(Booking, booking_id)
            if not booking:
                raise NotFoundError(detail=f"Booking with ID {booking_id} not found")

            if actor.role == UserRole.STUDENT and booking.user_id != actor.id:
                raise PermissionDeniedError(detail="Students are only authorized to return their own bookings")

            if booking.status != BookingStatus.APPROVED:
                raise ValidationError(detail=f"Only approved reservations can be returned (current: '{booking.status.value}')")

            booking.status = BookingStatus.RETURNED
            self.audit_log_repository.log(
                session=session,
                user_id=actor.id,
                action="BOOKING_RETURN",
                meta_data={"booking_id": booking.id, "returned_by": actor.id},
            )

            session.commit()
            session.refresh(booking)
            return booking

    def get_booking_by_id(self, booking_id: int, current_user: User) -> Booking:
        booking = self.booking_repository.get_by_id_or_raise(booking_id)
        if current_user.role == UserRole.STUDENT and booking.user_id != current_user.id:
            raise PermissionDeniedError(detail="Access to this booking record is restricted to the booking owner")
        return booking

    def list_bookings(
        self,
        current_user: User,
        status: Optional[BookingStatus] = None,
        resource_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        offset = (page - 1) * page_size
        # RBAC: students can ONLY ever see their own bookings
        effective_user_id = current_user.id if current_user.role == UserRole.STUDENT else None

        items = self.booking_repository.list_all_bookings(
            status=status,
            resource_id=resource_id,
            user_id=effective_user_id,
            offset=offset,
            limit=page_size,
        )

        filters = {}
        if status:
            filters["status"] = status
        if resource_id:
            filters["resource_id"] = resource_id
        if effective_user_id:
            filters["user_id"] = effective_user_id

        total_count = self.booking_repository.count(filters=filters)
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 0

        return {
            "items": items,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
