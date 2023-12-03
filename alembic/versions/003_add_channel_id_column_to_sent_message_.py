"""Add channel_id column to sent_message table

Revision ID: 003
Revises: 002
Create Date: 2023-12-03 16:21:28.361308

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('sent_message', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('channel_id', sa.Integer(), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table('sent_message', schema=None) as batch_op:
        batch_op.drop_column('channel_id')
