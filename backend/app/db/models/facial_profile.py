from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.db.base import Base, TimestampMixin

# ArcFace (InsightFace buffalo_l) embedding dimensionality.
EMBEDDING_DIM = 512


class FacialProfilePhoto(Base, TimestampMixin):
    """One reference face embedding for a member. The set of these rows = the
    member's facial profile. We store the embedding (and an optional small crop),
    NEVER the original uploaded/meeting photo."""

    __tablename__ = "facial_profile_photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(
        ForeignKey("bsg_members.id", ondelete="CASCADE"), index=True
    )
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
    # Small face thumbnail kept for display in Visitor Review (retained with profile).
    crop_path: Mapped[str | None] = mapped_column(nullable=True)
    # registration | visitor_map | visitor_promotion
    source: Mapped[str] = mapped_column(nullable=False, default="registration")

    member: Mapped["BSGMember"] = relationship(back_populates="photos")  # noqa: F821
