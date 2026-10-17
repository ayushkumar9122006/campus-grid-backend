from datetime import datetime, timedelta, timezone
import pytest
from pydantic import ValidationError

from campus_grid.schema.booking_schema import BookingCreate
from campus_grid.schema.resource_schema import ResourceCreate, ResourceUpdate
from campus_grid.schema.user_schema import UserRegister


def test_booking_create_valid():
    now = datetime.now(timezone.utc)
    start = now + timedelta(hours=1)
    end = now + timedelta(hours=3)

    schema = BookingCreate(resource_id=1, start_time=start, end_time=end)
    assert schema.resource_id == 1
    assert schema.end_time > schema.start_time


def test_booking_create_inverted_time():
    now = datetime.now(timezone.utc)
    start = now + timedelta(hours=3)
    end = now + timedelta(hours=1)

    with pytest.raises(ValidationError) as exc:
        BookingCreate(resource_id=1, start_time=start, end_time=end)
    assert "end_time must be strictly after start_time" in str(exc.value)


def test_booking_create_too_short():
    now = datetime.now(timezone.utc)
    start = now + timedelta(hours=1)
    end = start + timedelta(seconds=60)  # Only 1 min, min is 5 min

    with pytest.raises(ValidationError) as exc:
        BookingCreate(resource_id=1, start_time=start, end_time=end)
    assert "Booking duration must be at least 5 minutes" in str(exc.value)


def test_resource_create_valid():
    resource = ResourceCreate(
        name="VR Lab Headset Pro",
        category="lab_equipment",
        total_quantity=5,
    )
    assert resource.available_quantity == 5


def test_resource_create_available_exceeds_total():
    with pytest.raises(ValidationError) as exc:
        ResourceCreate(
            name="VR Lab Headset Pro",
            category="lab_equipment",
            total_quantity=2,
            available_quantity=5,
        )
    assert "available_quantity cannot exceed total_quantity" in str(exc.value)


def test_resource_create_negative_quantity():
    with pytest.raises(ValidationError):
        ResourceCreate(
            name="VR Headset",
            category="lab_equipment",
            total_quantity=0,
        )


def test_user_register_invalid_email():
    with pytest.raises(ValidationError) as exc:
        UserRegister(
            email="not-an-email",
            password="StrongPassword123!",
        )
    assert "Invalid email format" in str(exc.value)


def test_user_register_short_password():
    with pytest.raises(ValidationError) as exc:
        UserRegister(
            email="valid@campus.edu",
            password="short",
        )
    assert "at least 8 characters" in str(exc.value)
