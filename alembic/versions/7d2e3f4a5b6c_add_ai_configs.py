"""add_ai_configs

Revision ID: 7d2e3f4a5b6c
Revises: 5a1b2c3d4e5f
Create Date: 2026-08-14 00:00:00.000000

新增 ai_configs 表：每用户独立 AI 配置（provider/base_url/model/api_key 加密）。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d2e3f4a5b6c'
down_revision: Union[str, Sequence[str], None] = '5a1b2c3d4e5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create ai_configs table."""
    op.create_table(
        'ai_configs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=20), nullable=False),
        sa.Column('base_url', sa.String(length=500), nullable=True),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('api_key_encrypted', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.UniqueConstraint('user_id', name='uq_ai_configs_user_id'),
    )


def downgrade() -> None:
    """Drop ai_configs table."""
    op.drop_table('ai_configs')