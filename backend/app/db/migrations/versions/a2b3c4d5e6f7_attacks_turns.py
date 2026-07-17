"""attacks.turns (multi-turn attacks)

Revision ID: a2b3c4d5e6f7
Revises: 9a1f2c3d4e5b
Create Date: 2026-07-17 16:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, None] = "9a1f2c3d4e5b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "attacks",
        sa.Column("turns", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_column("attacks", "turns")
