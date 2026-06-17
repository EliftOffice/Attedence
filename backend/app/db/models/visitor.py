from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.db.base import Base, TimestampMixin
from app.db.models.facial_profile import EMBEDDING_DIM


class VisitorEntry(Base, TimestampMixin):
    """An unmatched real face from a meeting photo, pending leader review.

    Retention policy: there is NO time-based expiry. The crop is held only while
    status == 'pending' and is DELETED on review (regardless of outcome). The row
    itself is retained for visitor statistics. See services/visitors.py.

    status: pending | mapped_same | mapped_guest | moved | promoted | kept
    """

    __tablename__ = "visitor_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"), index=True
    )
    # Path to the stored crop while pending; nulled out once the crop is deleted.
    face_crop_path: Mapped[Optional[str]] = mapped_column(nullable=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, default="pending", index=True)
    resolved_member_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("bsg_members.id", ondelete="SET NULL"), nullable=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    meeting: Mapped["Meeting"] = relationship(back_populates="visitors")  # noqa: F821
