"""drop_health_articles_and_goals

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-11-19 15:05:00.000000

DB-2b：删除无业务引用的两张表（DB-2 报告评审通过，用户已批准）。
- health_articles：无 API/UI 引用，模型与 schema 一并移除
- user_health_goals：无 API/UI 引用，模型与 schema 一并移除
downgrade 按初始迁移定义重建表结构；表内数据恢复需依赖执行前备份。
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop the two unused tables (idempotent for dev DBs created via create_all)."""
    bind = op.get_bind()
    existing = set(sa.inspect(bind).get_table_names())
    if "user_health_goals" in existing:
        op.drop_table("user_health_goals")
    if "health_articles" in existing:
        op.drop_table("health_articles")


def downgrade() -> None:
    """Recreate table structures exactly as defined in the initial migration."""
    bind = op.get_bind()
    existing = set(sa.inspect(bind).get_table_names())
    if "health_articles" not in existing:
        op.create_table(
            "health_articles",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column("category", sa.String(50), nullable=True),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("author", sa.String(100), nullable=True),
            sa.Column("views", sa.Integer(), nullable=True),
            sa.Column("is_recommended", sa.Boolean(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
    if "user_health_goals" not in existing:
        op.create_table(
            "user_health_goals",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("goal_type", sa.String(50), nullable=False),
            sa.Column("target_value", sa.Float(), nullable=True),
            sa.Column("current_value", sa.Float(), nullable=True),
            sa.Column("start_date", sa.DateTime(), nullable=True),
            sa.Column("end_date", sa.DateTime(), nullable=True),
            sa.Column("status", sa.String(20), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
