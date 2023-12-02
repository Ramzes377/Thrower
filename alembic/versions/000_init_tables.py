"""Init functionality tables

Revision ID: 000
Revises: 
Create Date: 2023-10-15 15:48:59.604543

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import api.tables

revision: str = '000'
down_revision: Union[str, None] = None  # do not erase already existed data
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'activity_info',
        sa.Column('app_name', sa.Text(), nullable=True),
        sa.Column('icon_url', sa.Text(), nullable=True),
        sa.Column('app_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('app_id')
    )
    op.create_index(
        op.f('ix_activity_info_app_id'),
        'activity_info',
        ['app_id'],
        unique=True
    )

    op.create_table(
        'guild',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('initialized_channels', sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        op.f('ix_guild_id'),
        'guild',
        ['id'],
        unique=True
    )

    op.create_table(
        'member',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=True),
        sa.Column('default_sess_name', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        op.f('ix_member_id'),
        'member',
        ['id'],
        unique=True
    )

    op.create_table(
        'sent_message',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        op.f('ix_sent_message_id'),
        'sent_message',
        ['id'],
        unique=True
    )

    op.create_table(
        'session',
        sa.Column('name', sa.Text(), nullable=True),
        sa.Column('creator_id', sa.Integer(), nullable=True),
        sa.Column('leader_id', sa.Integer(), nullable=True),
        sa.Column('message_id', sa.Integer(), nullable=True),
        sa.Column('channel_id', sa.Integer(), nullable=False),
        sa.Column('begin', api.tables.DateTime(), nullable=False),
        sa.Column('end', api.tables.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('channel_id')
    )
    op.create_index(
        op.f('ix_session_channel_id'),
        'session',
        ['channel_id'],
        unique=False
    )

    op.create_table(
        'activity',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.Column('begin', api.tables.DateTime(),
                  nullable=False),
        sa.Column('end', api.tables.DateTime(),
                  nullable=True),
        sa.ForeignKeyConstraint(['id'], ['activity_info.app_id'], ),
        sa.ForeignKeyConstraint(['member_id'], ['member.id'], ),
        sa.PrimaryKeyConstraint('id', 'member_id', 'begin')
    )
    op.create_index(
        op.f('ix_activity_id'),
        'activity',
        ['id'],
        unique=False
    )
    op.create_index(
        op.f('ix_activity_member_id'),
        'activity',
        ['member_id'],
        unique=False
    )

    op.create_table(
        'favorite_music',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('counter', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['member.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'query')
    )
    op.create_index(
        op.f('ix_favorite_music_user_id'),
        'favorite_music',
        ['user_id'],
        unique=True
    )

    op.create_table(
        'leadership',
        sa.Column('channel_id', sa.Integer(), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.Column('begin', api.tables.DateTime(),
                  nullable=False),
        sa.Column('end', api.tables.DateTime(),
                  nullable=True),
        sa.ForeignKeyConstraint(['channel_id'],
                                ['session.channel_id'], ),
        sa.ForeignKeyConstraint(['member_id'], ['member.id'], ),
        sa.PrimaryKeyConstraint('channel_id', 'member_id', 'begin')
    )
    op.create_index(
        op.f('ix_leadership_channel_id'),
        'leadership',
        ['channel_id'],
        unique=True
    )

    op.create_table(
        'member_session',
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.Column('channel_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['channel_id'],
                                ['session.channel_id'], ),
        sa.ForeignKeyConstraint(['member_id'], ['member.id'], ),
        sa.PrimaryKeyConstraint('member_id', 'channel_id')
    )

    op.create_table(
        'prescence',
        sa.Column('channel_id', sa.Integer(), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.Column('begin', api.tables.DateTime(),
                  nullable=False),
        sa.Column('end', api.tables.DateTime(),
                  nullable=True),
        sa.ForeignKeyConstraint(['channel_id'],
                                ['session.channel_id'], ),
        sa.ForeignKeyConstraint(['member_id'], ['member.id'], ),
        sa.PrimaryKeyConstraint('channel_id', 'member_id', 'begin')
    )
    op.create_index(
        op.f('ix_prescence_channel_id'),
        'prescence',
        ['channel_id'],
        unique=True
    )

    op.create_table(
        'role',
        sa.Column('id', sa.Integer(), nullable=True),
        sa.Column('app_id', sa.Integer(), nullable=False),
        sa.Column('guild_id', sa.Integer(), nullable=False,
                  server_default=sa.text('257878464667844618')),
        sa.ForeignKeyConstraint(['app_id'],
                                ['activity_info.app_id'], ),
        sa.PrimaryKeyConstraint('app_id', 'guild_id'),
    )

    op.create_table(
        'emoji',
        sa.Column('id', sa.Integer(), nullable=True),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['role.id'], ),
        sa.PrimaryKeyConstraint('role_id')
    )


def downgrade() -> None:
    op.drop_table('emoji')
    op.drop_table('role')
    op.drop_index(op.f('ix_prescence_channel_id'), table_name='prescence')
    op.drop_table('prescence')
    op.drop_table('member_session')
    op.drop_index(op.f('ix_leadership_channel_id'), table_name='leadership')
    op.drop_table('leadership')
    op.drop_table('favorite_music')
    op.drop_index(op.f('ix_activity_member_id'), table_name='activity')
    op.drop_index(op.f('ix_activity_id'), table_name='activity')
    op.drop_table('activity')
    op.drop_index(op.f('ix_session_channel_id'), table_name='session')
    op.drop_table('session')
    op.drop_index(op.f('ix_sent_message_id'), table_name='sent_message')
    op.drop_table('sent_message')
    op.drop_index(op.f('ix_member_id'), table_name='member')
    op.drop_table('member')
    op.drop_index(op.f('ix_guild_id'), table_name='guild')
    op.drop_table('guild')
    op.drop_index(op.f('ix_activity_info_app_id'), table_name='activity_info')
    op.drop_table('activity_info')
