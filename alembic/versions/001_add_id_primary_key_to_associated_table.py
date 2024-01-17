"""add id primary key to associated table

Revision ID: 001
Revises: 000
Create Date: 2023-11-29 02:39:01.001495

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from src.app import tables
from src.config import Config

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = '000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

get_session_local = tables.SessionFabric.build(
    db_uri=Config.local_db_uri,
    connect_args={"check_same_thread": False, "timeout": 120},
    is_async=False
)


def upgrade() -> None:
    try:
        op.drop_table('_alembic_tmp_member_session')
    except OperationalError:
        pass

    session = next(get_session_local())

    statements = [
        """
        CREATE TABLE temp AS
        SELECT member_id, channel_id FROM member_session;
        """,
        """ALTER TABLE member_session RENAME TO member_session_temp;""",
        """
        CREATE TABLE member_session (
          id INTEGER PRIMARY KEY AUTOINCREMENT, 
          member_id INTEGER,
          channel_id INTEGER,
          CONSTRAINT FK_member_session_member FOREIGN KEY (member_id) REFERENCES "member"(id),
          CONSTRAINT FK_member_session_session_2 FOREIGN KEY (channel_id) REFERENCES "session"(channel_id));
        """,
        """
        INSERT INTO member_session (member_id, channel_id)
        SELECT member_id, channel_id FROM temp;
        """,
        """DROP TABLE temp; """,
        """DROP TABLE member_session_temp;""",
    ]
    for stmt in statements:
        with session.begin():
            session.execute(text(stmt))
    session.commit()

    with op.batch_alter_table('member_session', schema=None) as batch_op:
        batch_op.create_unique_constraint('idx_unique_member_session',
                                          ['member_id', 'channel_id'])
        batch_op.create_index(batch_op.f('ix_member_session_channel_id'),
                              ['channel_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_member_session_member_id'),
                              ['member_id'], unique=False)

    with op.batch_alter_table('prescence', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_prescence_member_id'),
                              ['member_id'], unique=False)

    with op.batch_alter_table('role', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_role_id'), ['id'],
                              unique=False)


def downgrade() -> None:
    with op.batch_alter_table('role', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_role_id'))

    with op.batch_alter_table('prescence', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_prescence_member_id'))

    with op.batch_alter_table('member_session', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_member_session_member_id'))
        batch_op.drop_index(batch_op.f('ix_member_session_channel_id'))
        batch_op.drop_constraint('idx_unique_member_session',
                                 type_='unique')
        batch_op.alter_column('channel_id',
                              existing_type=sa.INTEGER(),
                              nullable=True)
        batch_op.alter_column('member_id',
                              existing_type=sa.INTEGER(),
                              nullable=True)
        batch_op.drop_column('id')

    op.create_table('_alembic_tmp_member_session',
                    sa.Column('member_id', sa.INTEGER(), nullable=False),
                    sa.Column('channel_id', sa.INTEGER(), nullable=False),
                    sa.Column('id', sa.INTEGER(), nullable=False),
                    sa.ForeignKeyConstraint(['channel_id'],
                                            ['session.channel_id'], ),
                    sa.ForeignKeyConstraint(['member_id'], ['member.id'], ),
                    sa.PrimaryKeyConstraint('member_id', 'channel_id'),
                    sa.UniqueConstraint('member_id', 'channel_id',
                                        name='idx_unique_member_session')
                    )
