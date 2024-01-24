"""empty message

Revision ID: 004
Revises: 003
Create Date: 2024-01-16 23:03:27.558303

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import src.app.tables

revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('favorite_music', schema=None) as batch_op:
        batch_op.alter_column('title',
                              existing_type=sa.TEXT(),
                              type_=sa.String(),
                              nullable=False)


def downgrade() -> None:
    with op.batch_alter_table('favorite_music', schema=None) as batch_op:
        batch_op.alter_column('title',
                              existing_type=sa.String(),
                              type_=sa.TEXT(),
                              nullable=True)
