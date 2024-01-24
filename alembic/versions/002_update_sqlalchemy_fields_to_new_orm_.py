"""Update sqlalchemy fields to new ORM style

Revision ID: 002
Revises: 001
Create Date: 2023-12-03 02:11:40.954707

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('activity_info', schema=None) as batch_op:
        batch_op.alter_column('app_name',
                              existing_type=sa.TEXT(),
                              type_=sa.String(),
                              nullable=False)
        batch_op.alter_column('icon_url',
                              existing_type=sa.TEXT(),
                              type_=sa.String(),
                              nullable=False)

    with op.batch_alter_table('emoji', schema=None) as batch_op:
        batch_op.alter_column('id',
                              existing_type=sa.INTEGER(),
                              nullable=False)
        batch_op.create_index(batch_op.f('ix_emoji_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_emoji_role_id'), ['role_id'],
                              unique=False)

    with op.batch_alter_table('favorite_music', schema=None) as batch_op:
        batch_op.alter_column('counter',
                              existing_type=sa.INTEGER(),
                              nullable=False)

    with op.batch_alter_table('leadership', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_leadership_member_id'),
                              ['member_id'], unique=False)

    with op.batch_alter_table('member', schema=None) as batch_op:
        batch_op.alter_column('name',
                              existing_type=sa.TEXT(),
                              type_=sa.String(),
                              nullable=False)
        batch_op.alter_column('default_sess_name',
                              existing_type=sa.TEXT(),
                              type_=sa.String(),
                              existing_nullable=True)

    with op.batch_alter_table('member_session', schema=None) as batch_op:
        batch_op.alter_column('id',
                              existing_type=sa.INTEGER(),
                              nullable=False,
                              autoincrement=True)
        batch_op.alter_column('member_id',
                              existing_type=sa.INTEGER(),
                              nullable=False)
        batch_op.alter_column('channel_id',
                              existing_type=sa.INTEGER(),
                              nullable=False)

    with op.batch_alter_table('role', schema=None) as batch_op:
        batch_op.alter_column('id',
                              existing_type=sa.INTEGER(),
                              nullable=False)

    with op.batch_alter_table('sent_message', schema=None) as batch_op:
        batch_op.alter_column('guild_id',
                              existing_type=sa.INTEGER(),
                              nullable=False)

    with op.batch_alter_table('session', schema=None) as batch_op:
        batch_op.alter_column('name',
                              existing_type=sa.TEXT(),
                              type_=sa.String(),
                              nullable=False)
        batch_op.alter_column('creator_id',
                              existing_type=sa.INTEGER(),
                              nullable=False)
        batch_op.alter_column('leader_id',
                              existing_type=sa.INTEGER(),
                              nullable=False)
        batch_op.alter_column('message_id',
                              existing_type=sa.INTEGER(),
                              nullable=False)


def downgrade() -> None:
    with op.batch_alter_table('session', schema=None) as batch_op:
        batch_op.alter_column('message_id',
                              existing_type=sa.INTEGER(),
                              nullable=True)
        batch_op.alter_column('leader_id',
                              existing_type=sa.INTEGER(),
                              nullable=True)
        batch_op.alter_column('creator_id',
                              existing_type=sa.INTEGER(),
                              nullable=True)
        batch_op.alter_column('name',
                              existing_type=sa.String(),
                              type_=sa.TEXT(),
                              nullable=True)

    with op.batch_alter_table('sent_message', schema=None) as batch_op:
        batch_op.alter_column('guild_id',
                              existing_type=sa.INTEGER(),
                              nullable=True)

    with op.batch_alter_table('role', schema=None) as batch_op:
        batch_op.alter_column('id',
                              existing_type=sa.INTEGER(),
                              nullable=True)

    with op.batch_alter_table('member_session', schema=None) as batch_op:
        batch_op.alter_column('channel_id',
                              existing_type=sa.INTEGER(),
                              nullable=True)
        batch_op.alter_column('member_id',
                              existing_type=sa.INTEGER(),
                              nullable=True)
        batch_op.alter_column('id',
                              existing_type=sa.INTEGER(),
                              nullable=True,
                              autoincrement=True)

    with op.batch_alter_table('member', schema=None) as batch_op:
        batch_op.alter_column('default_sess_name',
                              existing_type=sa.String(),
                              type_=sa.TEXT(),
                              existing_nullable=True)
        batch_op.alter_column('name',
                              existing_type=sa.String(),
                              type_=sa.TEXT(),
                              nullable=True)

    with op.batch_alter_table('leadership', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_leadership_member_id'))

    with op.batch_alter_table('favorite_music', schema=None) as batch_op:
        batch_op.alter_column('counter',
                              existing_type=sa.INTEGER(),
                              nullable=True)

    with op.batch_alter_table('emoji', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_emoji_role_id'))
        batch_op.drop_index(batch_op.f('ix_emoji_id'))
        batch_op.alter_column('id',
                              existing_type=sa.INTEGER(),
                              nullable=True)

    with op.batch_alter_table('activity_info', schema=None) as batch_op:
        batch_op.alter_column('icon_url',
                              existing_type=sa.String(),
                              type_=sa.TEXT(),
                              nullable=True)
        batch_op.alter_column('app_name',
                              existing_type=sa.String(),
                              type_=sa.TEXT(),
                              nullable=True)
