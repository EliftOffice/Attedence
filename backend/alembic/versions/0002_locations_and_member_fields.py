"""cities, streets, and member surname/address fields

Revision ID: 0002_locations
Revises: 0001_initial
Create Date: 2026-06-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_locations"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cities",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "streets",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("city_id", sa.Integer, sa.ForeignKey("cities.id", ondelete="CASCADE")),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_streets_city_id", "streets", ["city_id"])

    op.add_column("bsg_members", sa.Column("surname", sa.String, nullable=True))
    op.add_column(
        "bsg_members",
        sa.Column("city_id", sa.Integer, sa.ForeignKey("cities.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column(
        "bsg_members",
        sa.Column("street_id", sa.Integer, sa.ForeignKey("streets.id", ondelete="SET NULL"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("bsg_members", "street_id")
    op.drop_column("bsg_members", "city_id")
    op.drop_column("bsg_members", "surname")
    op.drop_index("ix_streets_city_id", table_name="streets")
    op.drop_table("streets")
    op.drop_table("cities")
