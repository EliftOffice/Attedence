from datetime import date

from sqlalchemy import Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Meeting(Base, TimestampMixin):
    """A group's session on a date. One meeting per (group, date)."""

    __tablename__ = "meetings"
    __table_args__ = (UniqueConstraint("bsg_id", "meeting_date", name="uq_meeting_group_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    bsg_id: Mapped[int] = mapped_column(ForeignKey("bsgs.id", ondelete="CASCADE"), index=True)
    meeting_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    # telegram | test_endpoint | manual
    source: Mapped[str] = mapped_column(nullable=False, default="telegram")

    attendance: Mapped[list["AttendanceRecord"]] = relationship(  # noqa: F821
        back_populates="meeting", cascade="all, delete-orphan"
    )
    visitors: Mapped[list["VisitorEntry"]] = relationship(  # noqa: F821
        back_populates="meeting", cascade="all, delete-orphan"
    )
