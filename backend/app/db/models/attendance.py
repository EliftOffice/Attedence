from typing import Optional

from sqlalchemy import Boolean, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class AttendanceRecord(Base, TimestampMixin):
    """A member present at a meeting. Present-once (unique per meeting+member);
    re-running recognition is idempotent.

    `is_guest` is stored at write time: true when the member attended a meeting
    of a group other than his home group and was NOT moved into it.
    """

    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint("meeting_id", "member_id", name="uq_attendance_meeting_member"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"), index=True
    )
    member_id: Mapped[int] = mapped_column(
        ForeignKey("bsg_members.id", ondelete="CASCADE"), index=True
    )
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # auto | visitor_resolution | manual
    method: Mapped[str] = mapped_column(nullable=False, default="auto")
    is_guest: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    meeting: Mapped["Meeting"] = relationship(back_populates="attendance")  # noqa: F821
    member: Mapped["BSGMember"] = relationship()  # noqa: F821
