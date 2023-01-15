import asyncio
import re
from typing import Awaitable

import discord
from discord.ext import commands

from api.rest.base import request
from .misc import get_category


class BaseCogMixin(commands.Cog):

    def __init__(self, bot, silent=False):
        super(BaseCogMixin, self).__init__()
        self.bot = bot
        if not silent:
            print(f'Cog {type(self).__name__} have been started!')

    def exist(self, obj: dict):
        return obj is not None and 'detail' not in obj

    @staticmethod
    async def request(url: str, method: str = 'get', data: dict | None = None):
        return await request(url, method, data)

    async def log_message(self, send: Awaitable):
        msg = await send
        await self.request(f'sent_message/', 'post', data={'id': msg.id})
        return msg


class DiscordFeaturesMixin(BaseCogMixin):

    async def get_session(self, channel_id: int) -> dict | None:
        session = await self.request(f'session/{channel_id}')
        if self.exist(session):
            return session
        return None

    async def get_user_channel(self, user_id: int) -> discord.VoiceChannel | None:
        session = await self.request(f'session/unclosed/{user_id}')
        if self.exist(session):
            return self.bot.get_channel(session['channel_id'])
        return None

    async def get_user_sess_name(self, user: discord.member.Member) -> str:
        if user.activity and user.activity.type is discord.ActivityType.playing:
            sess_name = f"[{re.compile('[^a-zA-Z0-9а-яА-Я +]').sub('', user.activity.name)}]"
        else:
            member = await self.request(f'user/{user.id}')
            if self.exist(member) and member.get('default_sess_name'):
                sess_name = member['default_sess_name']
            else:
                session = await self.request(f'session/unclosed/{user.id}')
                sess_name = session['name'] if self.exist(session) else f"Сессия {user.display_name}'а"
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
