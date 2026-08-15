"""add_vision_columns_to_ai_configs

Revision ID: 8e4f5a6b7c8d
Revises: 7d2e3f4a5b6c
Create Date: 2026-08-14 00:10:00.000000

ai_configs 增加舌诊视觉模型列（vision_provider/base_url/model/api_key_encrypted）。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8e4f5a6b7c8d'
down_revision: Union[str, Sequence[str], None] = '7d2e3f4a5b6c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add vision model columns to ai_configs."""
    with op.batch_alter_table('ai_configs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('vision_provider', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('vision_base_url', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('vision_model', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('vision_api_key_encrypted', sa.String(length=1000), nullable=True))


def downgrade() -> None:
    """Drop vision model columns."""
    with op.batch_alter_table('ai_configs', schema=None) as batch_op:
        batch_op.drop_column('vision_api_key_encrypted')
        batch_op.drop_column('vision_model')
        batch_op.drop_column('vision_base_url')
        batch_op.drop_column('vision_provider')