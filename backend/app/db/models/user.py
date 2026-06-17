from typing import Optional

from sqlalchemy import Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """Login account. Identified by MOBILE NUMBER (not email). Roles: admin | leader."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    mobile_number: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[str] = mapped_column(nullable=False, default="leader")  # admin | leader
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    leader: Mapped[Optional["BSGLeader"]] = relationship(  # noqa: F821
        back_populates="user", uselist=False
    )
