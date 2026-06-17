from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class BSGLeader(Base, TimestampMixin):
    """A leader assigned to exactly one BSG, linked to a login User.

    The Telegram identity is captured at registration via the bot-DM link flow
    (the leader sends a one-time `telegram_link_code` to the bot). A user's private
    chat id equals their user id, which is also the sender id on a GROUP message,
    so `telegram_user_id` is what we match on later. See services/leader_resolver.py.
    """

    __tablename__ = "bsg_leaders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    bsg_id: Mapped[int] = mapped_column(ForeignKey("bsgs.id", ondelete="CASCADE"), unique=True)
    name: Mapped[str] = mapped_column(nullable=False)

    # Telegram identity (nullable until linked).
    telegram_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, index=True, nullable=True)
    telegram_chat_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    telegram_link_code: Mapped[Optional[str]] = mapped_column(index=True, nullable=True)
    telegram_linked_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    user: Mapped["User"] = relationship(back_populates="leader")  # noqa: F821
    bsg: Mapped["BibleStudyGroup"] = relationship(back_populates="leader")  # noqa: F821
