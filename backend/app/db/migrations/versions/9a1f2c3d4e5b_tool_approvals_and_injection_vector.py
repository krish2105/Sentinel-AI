"""tool_approvals table + attacks.injection_vector

Revision ID: 9a1f2c3d4e5b
Revises: 8358ec8fb7dc
Create Date: 2026-07-17 15:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "9a1f2c3d4e5b"
down_revision: Union[str, None] = "8358ec8fb7dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tool_approvals",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("target_id", sa.String(), nullable=True),
        sa.Column("target_name", sa.String(), nullable=False),
        sa.Column("tool_name", sa.String(), nullable=False),
        sa.Column("risk", sa.String(), nullable=False),
        sa.Column("arguments", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("owasp_ref", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("decided_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tool_approvals_user_id", "tool_approvals", ["user_id"])
    op.create_index("ix_tool_approvals_target_id", "tool_approvals", ["target_id"])
    op.add_column(
        "attacks",
        sa.Column(
            "injection_vector", sa.String(), nullable=False, server_default="direct"
        ),
    )


def downgrade() -> None:
    op.drop_column("attacks", "injection_vector")
    op.drop_index("ix_tool_approvals_target_id", table_name="tool_approvals")
    op.drop_index("ix_tool_approvals_user_id", table_name="tool_approvals")
    op.drop_table("tool_approvals")
