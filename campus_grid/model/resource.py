import enum
from typing import List, TYPE_CHECKING
from sqlalchemy import Enum as SAEnum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from campus_grid.model.base_model import TimeStampedModel

if TYPE_CHECKING:
    from campus_grid.model.booking import Booking


class ResourceCategory(str, enum.Enum):
    LAB_EQUIPMENT = "lab_equipment"
    MEDIA_GEAR = "media_gear"
    FACILITY = "facility"


class ResourceStatus(str, enum.Enum):
    AVAILABLE = "available"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"


class Resource(TimeStampedModel):
    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    total_quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    available_quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        default=ResourceStatus.AVAILABLE.value,
        nullable=False,
    )

    # Relationships
    bookings: Mapped[List["Booking"]] = relationship(
        "Booking",
        back_populates="resource",
        cascade="all, delete-orphan",
    )
