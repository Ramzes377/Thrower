import asyncio
import re

import discord
from discord.ext import commands
from fastapi.testclient import TestClient

from api.rest.base import app
from api.bot.misc import get_category


class BaseCogMixin(commands.Cog):

    def __init__(self, bot, silent=False):
        super(BaseCogMixin, self).__init__()
        self._client = TestClient(app)
        self.bot = bot
        if not silent:
            print(f'Cog {type(self).__name__} have been started!')

    def _object_exist(self, obj: dict):
        return obj is not None and 'detail' not in obj


class DiscordFeaturesMixin(BaseCogMixin):

    def get_session(self, channel_id: int):
        session = self._client.get(f'v1/session/{channel_id}').json()
        if self._object_exist(session):
            return session
        print(f"Can't find session {channel_id}")
        return None

    def get_user_channel(self, user_id: int) -> discord.VoiceChannel | None:
        session = self._client.get(f'v1/session/by_leader/{user_id}').json()
        if self._object_exist(session):
            return self.bot.get_channel(session['channel_id'])
        return None

    def get_user_sess_name(self, user: discord.member.Member) -> str:
        if user.activity and user.activity.type == discord.ActivityType.playing:
            sess_name = f"[{re.compile('[^a-zA-Z0-9а-яА-Я +]').sub('', user.activity.name)}]"
        else:
            member = self._client.get(f'v1/user/{user.id}').json()
            if 'detail' not in member and member.get('default_sess_name'):
                sess_name = member['default_sess_name']
            else:
                sess_name = f"{user.display_name}'s " f"channel"
        return sess_name

    async def edit_channel_name_category(self, user: discord.member.Member, channel: discord.VoiceChannel,
                                         overwrites=None) -> None:
        channel_name = self.get_user_sess_name(user)
        category = get_category(user)
        try:
            await asyncio.wait_for(
                channel.edit(name=channel_name, category=category, overwrites=overwrites),
                timeout=5.0
            )
        except asyncio.TimeoutError:  # Trying to rename channel in transfer but Discord restrictions :('
            await channel.edit(category=category, overwrites=overwrites)
