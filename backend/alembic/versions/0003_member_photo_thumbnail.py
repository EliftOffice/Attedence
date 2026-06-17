"""member facial-profile thumbnail path

Revision ID: 0003_member_thumb
Revises: 0002_locations
Create Date: 2026-06-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_member_thumb"
down_revision: Union[str, None] = "0002_locations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("facial_profile_photos", sa.Column("crop_path", sa.String, nullable=True))


def downgrade() -> None:
    op.drop_column("facial_profile_photos", "crop_path")
