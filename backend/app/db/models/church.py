from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Church(Base, TimestampMixin):
    __tablename__ = "churches"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)

    groups: Mapped[list["BibleStudyGroup"]] = relationship(  # noqa: F821
        back_populates="church", cascade="all, delete-orphan"
    )
