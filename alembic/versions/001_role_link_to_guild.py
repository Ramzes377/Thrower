"""Init functionality tables

Revision ID: 000
Revises:
Create Date: 2023-10-15 15:48:59.604543

"""
from contextlib import suppress
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.exc import OperationalError

import api.tables

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = '000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with suppress(OperationalError):
        op.add_column(
            'role',
            sa.Column('guild_id', sa.Integer(), nullable=True)
        )


def downgrade() -> None:
    op.drop_column('role', 'guild_id')
