"""add_daily_actions

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-11-21 14:20:00.000000

今日一件小事：每人每天一条行动记录。
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: str | Sequence[str] | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create daily_actions (idempotent for dev DBs created via create_all)."""
    bind = op.get_bind()
    existing = set(sa.inspect(bind).get_table_names())
    if "daily_actions" in existing:
        return
    op.create_table(
        "daily_actions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action_date", sa.Date(), nullable=False),
        sa.Column("action_key", sa.String(32), nullable=False),
        sa.Column("kind", sa.String(16), nullable=True),
        sa.Column("title", sa.String(80), nullable=False),
        sa.Column("description", sa.String(240), nullable=False),
        sa.Column("reason", sa.String(240), nullable=False),
        sa.Column("cta_label", sa.String(40), nullable=False),
        sa.Column("cta_path", sa.String(120), nullable=False),
        sa.Column("can_complete", sa.Boolean(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("user_id", "action_date", name="uq_daily_action_user_date"),
    )
    op.create_index("ix_daily_action_user_date", "daily_actions", ["user_id", "action_date"])
    op.create_index("ix_daily_actions_id", "daily_actions", ["id"])


def downgrade() -> None:
    """Drop daily_actions."""
    bind = op.get_bind()
    existing = set(sa.inspect(bind).get_table_names())
    if "daily_actions" in existing:
        op.drop_table("daily_actions")
