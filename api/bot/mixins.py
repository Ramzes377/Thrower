import asyncio
import re
from contextlib import suppress
from typing import Awaitable

import discord
from discord.ext import commands

from settings import bots_ids, logger
from .requests import BasicRequests

sess_re = re.compile('[^a-zA-Z0-9а-яА-Я +]')


class BaseCogMixin(commands.Cog):
    db = BasicRequests()

    def __init__(self, bot, sub_cog=False):
        super(BaseCogMixin, self).__init__()
        self.bot = bot
        if not sub_cog:
            logger.info(f'Cog {type(self).__name__} have been started!')

    @staticmethod
    def get_app_id(user: discord.Member) -> int | None:
        with suppress(AttributeError):
            return user.activity.application_id

    @staticmethod
    def user_is_playing(user: discord.Member) -> bool:
        return user.activity and user.activity.type == discord.ActivityType.playing


class DiscordFeaturesMixin(BaseCogMixin):

    async def get_user_channel(self, user_id: int) -> discord.VoiceChannel | \
                                                      None:
        session = await self.db.get_user_session(user_id)
        if session is None:
            return
        return self.bot.get_channel(session['channel_id'])

    async def get_user_sess_name(self, user: discord.Member) -> str:
        if user.activity and user.activity.type is discord.ActivityType.playing:
            sess_name = f"[{sess_re.sub('', user.activity.name)}]"
        else:
            member = await self.db.get_member(user.id)
            if member and member.get('default_sess_name'):
                sess_name = member['default_sess_name']
            else:
                session = await self.db.get_user_session(user.id)
                sess_name = session['name'] if session else f"Сессия {user.display_name}'а"
        return sess_name

    @staticmethod
    def _is_empty_channel(channel: discord.VoiceChannel):
        members = channel.members
        is_empty = len(members) == 0
        return True if is_empty else all(
            channel.guild.get_member(_id) in members for _id in bots_ids
        )

    def get_category(self, user: discord.Member) -> discord.CategoryChannel:
        activity_type = user.activity.type if user.activity else None
        return self.bot.categories.get(activity_type, self.bot.categories[None])

    async def edit_channel_name_category(
            self,
            user: discord.Member,
            channel: discord.VoiceChannel,
            overwrites=None,
            check_user=False
    ) -> None:

        if check_user:
            # calling of itself handler
            sess = await self.db.get_session(channel.id)
            if not sess or sess['leader_id'] != user.id or \
                    sess['end'] is not None:
                # check for call isn't deprecated
                return

        channel_name = await self.get_user_sess_name(user)
        category = self.get_category(user)
        coro = channel.edit(name=channel_name, category=category,
                            overwrites=overwrites)
        try:
            await asyncio.wait_for(coro, timeout=5.0)
            # Discord had set the rate limit for things like channel rename to 2 requests per 10 minutes
        except asyncio.TimeoutError:  # Trying to rename channel in transfer but Discord restrictions :(
            await channel.edit(category=category, overwrites=overwrites)
            await asyncio.sleep(10 * 60)  # after 10 minutes trying to update name again
            await self.edit_channel_name_category(user, channel, overwrites,
                                                  check_user=True)

    async def log_message(self, sendable: Awaitable):
        msg = await sendable
        await self.db.request(f'sent_message/', 'post', data={'id': msg.id})
        return msg
