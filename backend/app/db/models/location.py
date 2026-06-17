"""Admin-managed address lookups: City and Street (Street belongs to a City).

Members reference these as optional dropdown values. Admins add the allowed
values; leaders only pick from them.
"""
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class City(Base, TimestampMixin):
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False, unique=True)

    streets: Mapped[list["Street"]] = relationship(
        back_populates="city", cascade="all, delete-orphan"
    )


class Street(Base, TimestampMixin):
    __tablename__ = "streets"

    id: Mapped[int] = mapped_column(primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(nullable=False)

    city: Mapped["City"] = relationship(back_populates="streets")
