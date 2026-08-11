"""add_is_admin

Revision ID: e88188fefe67
Revises: f70bc89e0a56
Create Date: 2026-06-05 22:27:51.398202

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e88188fefe67'
down_revision: Union[str, Sequence[str], None] = 'f70bc89e0a56'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_admin column to users table."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_admin', sa.Boolean(), nullable=True))


def downgrade() -> None:
    """Remove is_admin column from users table."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('is_admin')
