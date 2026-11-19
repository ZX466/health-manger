"""add_async_tasks

Revision ID: a1b2c3d4e5f6
Revises: 9f1a2b3c4d5e
Create Date: 2026-11-19 11:52:00.000000

新增异步任务持久化表 async_tasks：
- task_id 唯一、user_id 归属、status(pending/running/completed/failed)
- payload 仅存消息列表，不存 LLM 配置，避免用户 API Key 明文落库
- claim_token 支持跨进程原子领取；启动时把中断的 running 任务标记为 failed
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "9f1a2b3c4d5e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create async_tasks table (idempotent for dev DBs created via create_all)."""
    bind = op.get_bind()
    if "async_tasks" not in set(sa.inspect(bind).get_table_names()):
        op.create_table(
            "async_tasks",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("task_id", sa.String(length=32), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
            sa.Column("payload", sa.Text(), nullable=False),
            sa.Column("result", sa.Text(), nullable=True),
            sa.Column("error", sa.String(length=200), nullable=True),
            sa.Column("claim_token", sa.String(length=32), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("claimed_at", sa.DateTime(), nullable=True),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.id"],
            ),
            sa.UniqueConstraint("task_id", name="uq_async_tasks_task_id"),
        )
    index_names = {index["name"] for index in sa.inspect(bind).get_indexes("async_tasks")}
    if "ix_async_tasks_task_id" not in index_names:
        op.create_index("ix_async_tasks_task_id", "async_tasks", ["task_id"], unique=False)
    if "ix_async_tasks_user_status" not in index_names:
        op.create_index(
            "ix_async_tasks_user_status", "async_tasks", ["user_id", "status"], unique=False
        )


def downgrade() -> None:
    """Drop async_tasks indexes and table."""
    op.drop_index("ix_async_tasks_user_status", table_name="async_tasks")
    op.drop_index("ix_async_tasks_task_id", table_name="async_tasks")
    op.drop_table("async_tasks")
