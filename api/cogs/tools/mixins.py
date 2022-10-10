import asyncio
import re

import aiohttp
import discord
from discord.ext import commands
from asyncio_extras import async_contextmanager

from api.cogs.tools.utils import get_category, send_removable_message


class BaseCogMixin(commands.Cog):
    def __init__(self, bot):
        super(BaseCogMixin, self).__init__()
        self.bot = bot
        print(f'Cog {type(self).__name__} have been started!')


class ConnectionMixin:
    bot = None

    def set_bot(self, bot):
        self.bot = bot

    @async_contextmanager
    async def get_connection(self) -> None:
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cur:
                yield cur

    @async_contextmanager
    async def url_request(self, url: str) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                yield response

    async def execute_sql(self, *scripts: str, fetch_all: bool = False) -> list[tuple[tuple]] | list[str | int | float]:
        results = []
        async with self.get_connection() as cur:
            for script in scripts:
                await cur.execute(script)
                try:
                    result = await cur.fetchall()
                    results.append(result if fetch_all or not result else result[0])
                except Exception as e:
                    results.append(e)
        return results[0] if not fetch_all and len(scripts) == 1 else results


class DiscordFeaturesMixin(ConnectionMixin):
    async def get_user_channel(self, user_id: int) -> discord.VoiceChannel | None:
        channel_id = await self.execute_sql(f"SELECT channel_id FROM CreatedSessions WHERE user_id = {user_id}")
        if channel_id:
            return self.bot.get_channel(*channel_id)

    async def get_user_sess_name(self, user: discord.member.Member) -> str:
        if user.activity and user.activity.type == discord.ActivityType.playing:
            sess_name = f"[{re.compile('[^a-zA-Z0-9а-яА-Я +]').sub('', user.activity.name)}]"
        else:
            have_default = await self.execute_sql(f'SELECT name FROM UserDefaultSessionName WHERE user_id = {user.id}')
            sess_name = have_default[0] if have_default and have_default[0] else f"{user.display_name}'s channel"
        return sess_name

    async def edit_channel_name_category(self, user: discord.member.Member, channel: discord.VoiceChannel, overwrites=None) -> None:
        channel_name = await self.get_user_sess_name(user)
        category = get_category(user)
        try:
            await asyncio.wait_for(channel.edit(name=channel_name, category=category, overwrites=overwrites), timeout=5.0)
        except asyncio.TimeoutError:  # Trying to rename channel in transfer but Discord restrictions :('
            await channel.edit(category=category)
