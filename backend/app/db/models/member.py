from datetime import date
from typing import Optional

from sqlalchemy import Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class BSGMember(Base, TimestampMixin):
    """A member belonging to a (home) BSG. `bsg_id` is mutable: a Visitor-Review
    'move to this group' action reassigns it (and writes a BSGMembershipHistory row)."""

    __tablename__ = "bsg_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    bsg_id: Mapped[int] = mapped_column(ForeignKey("bsgs.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(nullable=False)  # only required field
    surname: Mapped[Optional[str]] = mapped_column(nullable=True)
    mobile_number: Mapped[Optional[str]] = mapped_column(nullable=True)
    # Address (admin-managed dropdowns); both optional.
    city_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("cities.id", ondelete="SET NULL"), nullable=True
    )
    street_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("streets.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(nullable=False, default="active")  # active | inactive
    joined_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    bsg: Mapped["BibleStudyGroup"] = relationship(back_populates="members")  # noqa: F821
    city: Mapped[Optional["City"]] = relationship()  # noqa: F821
    street: Mapped[Optional["Street"]] = relationship()  # noqa: F821
    photos: Mapped[list["FacialProfilePhoto"]] = relationship(  # noqa: F821
        back_populates="member", cascade="all, delete-orphan"
    )
