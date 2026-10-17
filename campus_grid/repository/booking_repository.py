from contextlib import AbstractContextManager
from datetime import datetime
from typing import Callable, List, Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from campus_grid.model.booking import Booking, BookingStatus
from campus_grid.repository.base_repository import BaseRepository


class BookingRepository(BaseRepository[Booking]):
    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]]):
        super().__init__(session_factory, Booking)

    def count_overlapping_bookings(
        self,
        session: Session,
        resource_id: int,
        start_time: datetime,
        end_time: datetime,
        exclude_booking_id: Optional[int] = None,
    ) -> int:
        """Count active reservations overlapping with [start_time, end_time] for the resource."""
        stmt = (
            select(func.count(Booking.id))
            .where(
                Booking.resource_id == resource_id,
                Booking.status.in_([BookingStatus.PENDING, BookingStatus.APPROVED]),
                Booking.start_time < end_time,
                Booking.end_time > start_time,
            )
        )
        if exclude_booking_id is not None:
            stmt = stmt.where(Booking.id != exclude_booking_id)

        return session.scalar(stmt) or 0

    def get_user_bookings(self, user_id: int, offset: int = 0, limit: int = 20) -> List[Booking]:
        with self.session_factory() as session:
            stmt = (
                select(Booking)
                .options(joinedload(Booking.resource), joinedload(Booking.user))
                .where(Booking.user_id == user_id)
                .order_by(Booking.id.desc())
                .offset(offset)
                .limit(limit)
            )
            return list(session.scalars(stmt).all())

    def list_all_bookings(
        self,
        status: Optional[BookingStatus] = None,
        resource_id: Optional[int] = None,
        user_id: Optional[int] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> List[Booking]:
        with self.session_factory() as session:
            stmt = (
                select(Booking)
                .options(joinedload(Booking.resource), joinedload(Booking.user))
            )
            if status is not None:
                stmt = stmt.where(Booking.status == status)
            if resource_id is not None:
                stmt = stmt.where(Booking.resource_id == resource_id)
            if user_id is not None:
                stmt = stmt.where(Booking.user_id == user_id)

            stmt = stmt.order_by(Booking.id.desc()).offset(offset).limit(limit)
            return list(session.scalars(stmt).all())
