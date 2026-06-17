from datetime import date

from sqlalchemy import Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class BSGMembershipHistory(Base, TimestampMixin):
    """Records a member moving from one BSG to another (via Visitor-Review 'move to
    this group'). Keeps group growth / transfer reporting accurate.

    TODO: also seed an initial row on member creation if transfer-aware growth
    reporting needs the original group on record.
    """

    __tablename__ = "bsg_membership_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(
        ForeignKey("bsg_members.id", ondelete="CASCADE"), index=True
    )
    from_bsg_id: Mapped[int | None] = mapped_column(
        ForeignKey("bsgs.id", ondelete="SET NULL"), nullable=True
    )
    to_bsg_id: Mapped[int] = mapped_column(ForeignKey("bsgs.id", ondelete="CASCADE"))
    moved_on: Mapped[date] = mapped_column(Date, nullable=False)
