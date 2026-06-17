from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class BibleStudyGroup(Base, TimestampMixin):
    """A Bible Study Group (BSG), belonging to a church."""

    __tablename__ = "bsgs"

    id: Mapped[int] = mapped_column(primary_key=True)
    church_id: Mapped[int] = mapped_column(ForeignKey("churches.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(nullable=False)
    meeting_day: Mapped[Optional[str]] = mapped_column(nullable=True)  # e.g. "Wednesday"

    church: Mapped["Church"] = relationship(back_populates="groups")  # noqa: F821
    members: Mapped[list["BSGMember"]] = relationship(  # noqa: F821
        back_populates="bsg", cascade="all, delete-orphan"
    )
    leader: Mapped[Optional["BSGLeader"]] = relationship(  # noqa: F821
        back_populates="bsg", uselist=False
    )
