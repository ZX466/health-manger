"""add_mental_tables_and_persona_style

Revision ID: 9f1a2b3c4d5e
Revises: 8e4f5a6b7c8d
Create Date: 2026-11-15 16:50:00.000000

新增心理模块数据层：
- mental_records：心理每日打卡（uq_mental_user_date 唯一，ix_mental_user_date 索引）
- scale_assessments：PHQ-9/GAD-7 量表测评（ix_scale_user_type_time 索引）
- ai_configs.persona_style：心理关怀人设风格
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9f1a2b3c4d5e"
down_revision: str | Sequence[str] | None = "8e4f5a6b7c8d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create mental tables and add ai_configs.persona_style.

    Older local databases were created by SQLAlchemy ``create_all`` before this
    migration was stamped; on those the tables already exist. Keep the upgrade
    idempotent so ``alembic upgrade head`` repairs the schema instead of
    aborting on the first duplicate table.
    """
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "mental_records" not in tables:
        op.create_table(
            "mental_records",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("record_date", sa.Date(), nullable=False),
            sa.Column("mood_score", sa.Integer(), nullable=True),
            sa.Column("mood_label", sa.String(length=16), nullable=True),
            sa.Column("stress_tags", sa.Text(), nullable=True),
            sa.Column("sleep_hours", sa.Float(), nullable=True),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.id"],
            ),
            sa.UniqueConstraint("user_id", "record_date", name="uq_mental_user_date"),
        )
    mental_indexes = {index["name"] for index in sa.inspect(bind).get_indexes("mental_records")}
    if "ix_mental_user_date" not in mental_indexes:
        op.create_index(
            "ix_mental_user_date", "mental_records", ["user_id", "record_date"], unique=False
        )

    if "scale_assessments" not in tables:
        op.create_table(
            "scale_assessments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("scale_type", sa.String(length=8), nullable=False),
            sa.Column("answers", sa.Text(), nullable=True),
            sa.Column("score", sa.Integer(), nullable=True),
            sa.Column("risk_level", sa.String(length=20), nullable=True),
            sa.Column("crisis_flag", sa.Boolean(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.id"],
            ),
        )
    scale_indexes = {index["name"] for index in sa.inspect(bind).get_indexes("scale_assessments")}
    if "ix_scale_user_type_time" not in scale_indexes:
        op.create_index(
            "ix_scale_user_type_time",
            "scale_assessments",
            ["user_id", "scale_type", "created_at"],
            unique=False,
        )

    ai_columns = {column["name"] for column in sa.inspect(bind).get_columns("ai_configs")}
    if "persona_style" not in ai_columns:
        with op.batch_alter_table("ai_configs", schema=None) as batch_op:
            batch_op.add_column(
                sa.Column(
                    "persona_style", sa.String(length=16), nullable=False, server_default="humorous"
                )
            )


def downgrade() -> None:
    """Drop ai_configs.persona_style and mental tables."""
    with op.batch_alter_table("ai_configs", schema=None) as batch_op:
        batch_op.drop_column("persona_style")

    op.drop_index("ix_scale_user_type_time", table_name="scale_assessments")
    op.drop_table("scale_assessments")

    op.drop_index("ix_mental_user_date", table_name="mental_records")
    op.drop_table("mental_records")
