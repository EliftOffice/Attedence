"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 512


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "churches",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "bsgs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("church_id", sa.Integer, sa.ForeignKey("churches.id", ondelete="CASCADE")),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("meeting_day", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("mobile_number", sa.String, nullable=False),
        sa.Column("password_hash", sa.String, nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("role", sa.String, nullable=False, server_default="leader"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_mobile_number", "users", ["mobile_number"], unique=True)

    op.create_table(
        "bsg_leaders",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True
        ),
        sa.Column("bsg_id", sa.Integer, sa.ForeignKey("bsgs.id", ondelete="CASCADE"), unique=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger, nullable=True),
        sa.Column("telegram_chat_id", sa.BigInteger, nullable=True),
        sa.Column("telegram_link_code", sa.String, nullable=True),
        sa.Column("telegram_linked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_bsg_leaders_telegram_user_id", "bsg_leaders", ["telegram_user_id"])
    op.create_index("ix_bsg_leaders_telegram_link_code", "bsg_leaders", ["telegram_link_code"])

    op.create_table(
        "bsg_members",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("bsg_id", sa.Integer, sa.ForeignKey("bsgs.id", ondelete="CASCADE")),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("mobile_number", sa.String, nullable=True),
        sa.Column("status", sa.String, nullable=False, server_default="active"),
        sa.Column("joined_at", sa.Date, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_bsg_members_bsg_id", "bsg_members", ["bsg_id"])

    op.create_table(
        "facial_profile_photos",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "member_id", sa.Integer, sa.ForeignKey("bsg_members.id", ondelete="CASCADE")
        ),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
        sa.Column("source", sa.String, nullable=False, server_default="registration"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_facial_profile_photos_member_id", "facial_profile_photos", ["member_id"])

    op.create_table(
        "meetings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("bsg_id", sa.Integer, sa.ForeignKey("bsgs.id", ondelete="CASCADE")),
        sa.Column("meeting_date", sa.Date, nullable=False),
        sa.Column("source", sa.String, nullable=False, server_default="telegram"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("bsg_id", "meeting_date", name="uq_meeting_group_date"),
    )
    op.create_index("ix_meetings_bsg_id", "meetings", ["bsg_id"])
    op.create_index("ix_meetings_meeting_date", "meetings", ["meeting_date"])

    op.create_table(
        "attendance_records",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("meeting_id", sa.Integer, sa.ForeignKey("meetings.id", ondelete="CASCADE")),
        sa.Column(
            "member_id", sa.Integer, sa.ForeignKey("bsg_members.id", ondelete="CASCADE")
        ),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("method", sa.String, nullable=False, server_default="auto"),
        sa.Column("is_guest", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("meeting_id", "member_id", name="uq_attendance_meeting_member"),
    )
    op.create_index("ix_attendance_meeting_id", "attendance_records", ["meeting_id"])
    op.create_index("ix_attendance_member_id", "attendance_records", ["member_id"])

    op.create_table(
        "visitor_entries",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("meeting_id", sa.Integer, sa.ForeignKey("meetings.id", ondelete="CASCADE")),
        sa.Column("face_crop_path", sa.String, nullable=True),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
        sa.Column("status", sa.String, nullable=False, server_default="pending"),
        sa.Column(
            "resolved_member_id",
            sa.Integer,
            sa.ForeignKey("bsg_members.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_visitor_entries_meeting_id", "visitor_entries", ["meeting_id"])
    op.create_index("ix_visitor_entries_status", "visitor_entries", ["status"])

    op.create_table(
        "bsg_membership_history",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "member_id", sa.Integer, sa.ForeignKey("bsg_members.id", ondelete="CASCADE")
        ),
        sa.Column("from_bsg_id", sa.Integer, sa.ForeignKey("bsgs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("to_bsg_id", sa.Integer, sa.ForeignKey("bsgs.id", ondelete="CASCADE")),
        sa.Column("moved_on", sa.Date, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_bsg_membership_history_member_id", "bsg_membership_history", ["member_id"]
    )


def downgrade() -> None:
    op.drop_table("bsg_membership_history")
    op.drop_table("visitor_entries")
    op.drop_table("attendance_records")
    op.drop_table("meetings")
    op.drop_table("facial_profile_photos")
    op.drop_table("bsg_members")
    op.drop_table("bsg_leaders")
    op.drop_index("ix_users_mobile_number", table_name="users")
    op.drop_table("users")
    op.drop_table("bsgs")
    op.drop_table("churches")
