import asyncio
import re
from contextlib import suppress
from typing import Awaitable, TYPE_CHECKING, Optional

from discord import ActivityType, NotFound
from discord.ext import commands

from src.constants import constants
from .requests import BasicRequests
from src.utils import request, logger


if TYPE_CHECKING:
    from discord import Member, VoiceChannel, CategoryChannel

sess_re = re.compile('[^a-zA-Z0-9а-яА-Я +]')


class BaseCogMixin(commands.Cog):
    db = BasicRequests()

    def __init__(self, bot, sub_cog=False):
        super(BaseCogMixin, self).__init__()
        self.bot = bot
        if not sub_cog:
            logger.critical(constants.cog_started(name=type(self).__name__))

    @staticmethod
    def get_app_id(user: 'Member') -> int | None:
        with suppress(AttributeError):
            return user.activity.application_id

    @staticmethod
    def user_is_playing(user: 'Member') -> bool:
        activity = user.activity
        return activity and activity.type == ActivityType.playing


class DiscordFeaturesMixin(BaseCogMixin):

    async def get_user_channel(
        self,
        user_id: int
    ) -> Optional['VoiceChannel']:
        session = await self.db.get_user_session(user_id)
        if session is None:
            return
        return self.bot.get_channel(session['channel_id'])

    async def get_user_sess_name(self, user: 'Member') -> str:
        member = await self.db.get_member(user.id)
        if member and member.get('default_sess_name'):
            sess_name = member['default_sess_name']
        else:
            session = await self.db.get_user_session(user.id)
            sess_name = session['name'] if session else constants.session_name(name=user.display_name)
        return sess_name

    @staticmethod
    def _is_empty_channel(channel: 'VoiceChannel'):
        members = channel.members

        if len(members) == 0:   # empty channel
            return True

        return all(member.bot for member in members)

    def get_category(
            self,
            user: 'Member',
            guild_id: int
    ) -> 'CategoryChannel':

        channels = self.bot.guild_channels[guild_id]
        return channels.playing_category if user.activity else channels.idle_category

    async def edit_channel_name_category(
        self,
        user: 'Member',
        channel: 'VoiceChannel',
        overwrites=None,
    ) -> None:

        channel_name = await self.get_user_sess_name(user)
        category = self.get_category(user, channel.guild.id)
        coro = channel.edit(
            name=channel_name,
            category=category,
            overwrites=overwrites
        )
        try:
            # Discord had set the rate limit for things like channel rename
            # to 2 requests per 10 minutes
            with suppress(NotFound):
                await asyncio.wait_for(coro, timeout=15.0)
        except asyncio.TimeoutError:
            # Trying to rename channel in transfer but Discord restrictions :(
            with suppress(NotFound):
                await channel.edit(category=category, overwrites=overwrites)

    @staticmethod
    async def log_message(sendable: Awaitable):
        msg = await sendable
        with suppress(AttributeError):
            await request(f'sent_message', 'post', data={'id': msg.id})
        return msg
