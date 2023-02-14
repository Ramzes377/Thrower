import asyncio
import re
from typing import Awaitable

import discord
from discord.ext import commands

from .misc import get_category
from .requests import BasicRequests


class BaseCogMixin(commands.Cog):
    db = BasicRequests()

    def __init__(self, bot, subcog=False):
        super(BaseCogMixin, self).__init__()
        self.bot = bot
        if not subcog:
            print(f'Cog {type(self).__name__} have been started!')


class DiscordFeaturesMixin(BaseCogMixin):

    async def get_user_channel(self, user_id: int) -> discord.VoiceChannel | None:
        session = await self.db.get_user_session(user_id)
        return self.bot.get_channel(session['channel_id']) if self.db.exist(session) else None

    async def get_user_sess_name(self, user: discord.member.Member) -> str:
        if user.activity and user.activity.type is discord.ActivityType.playing:
            sess_name = f"[{re.compile('[^a-zA-Z0-9а-яА-Я +]').sub('', user.activity.name)}]"
        else:
            member = await self.db.get_member(user.id)
            if member.get('default_sess_name'):
                sess_name = member['default_sess_name']
            else:
                session = await self.db.get_user_session(user.id)
                sess_name = session['name'] if self.db.exist(session) else f"Сессия {user.display_name}'а"
        return sess_name

    async def edit_channel_name_category(self, user: discord.member.Member, channel: discord.VoiceChannel,
                                         overwrites=None) -> None:
        channel_name = await self.get_user_sess_name(user)
        category = get_category(user)
        try:
            await asyncio.wait_for(
                channel.edit(name=channel_name, category=category, overwrites=overwrites),
                timeout=5.0
            )
        except asyncio.TimeoutError:  # Trying to rename channel in transfer but Discord restrictions :('
            await channel.edit(category=category, overwrites=overwrites)
        except discord.NotFound:
            pass

    async def log_message(self, send: Awaitable):
        msg = await send
        await self.db.request(f'sent_message/', 'post', data={'id': msg.id})
        return msg
