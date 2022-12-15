import asyncio
import re

import discord
from discord.ext import commands

from api.bot.misc import get_category
from api.rest.v1.misc import request
from api.rest.v1.schemas import Session


class BaseCogMixin(commands.Cog):

    def __init__(self, bot, silent=False):
        super(BaseCogMixin, self).__init__()
        self.bot = bot
        if not silent:  # silent mod usually use for sub-cog modules
            print(f'Cog {type(self).__name__} have been started!')


class DiscordFeaturesMixin(BaseCogMixin):

    async def get_session(self, channel_id: int) -> Session | None:
        session = await request(f'session/{channel_id}')
        if session:
            return session
        return None

    async def get_user_channel(self, user_id: int) -> discord.VoiceChannel | None:
        session = await request(f'session/by_leader/{user_id}')
        if session:
            return self.bot.get_channel(session['channel_id'])
        return None

    async def get_user_sess_name(self, user: discord.member.Member) -> str:
        if user.activity and user.activity.type == discord.ActivityType.playing:
            sess_name = f"[{re.compile('[^a-zA-Z0-9а-яА-Я +]').sub('', user.activity.name)}]"
        else:
            member = await request(f'user/{user.id}')
            if 'detail' not in member and member.get('default_sess_name'):
                sess_name = member['default_sess_name']
            else:
                sess_name = f"{user.display_name}'s channel"
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
