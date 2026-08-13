"""add_unique_users_name

Revision ID: 5a1b2c3d4e5f
Revises: e88188fefe67
Create Date: 2026-08-13 00:00:00.000000

S13: users.name 增加唯一约束，防止并发/重名注册（配合注册端点 IntegrityError 兜底）。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a1b2c3d4e5f'
down_revision: Union[str, Sequence[str], None] = 'e88188fefe67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add unique constraint on users.name."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_users_name', ['name'])


def downgrade() -> None:
    """Drop unique constraint on users.name."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('uq_users_name', type_='unique')
