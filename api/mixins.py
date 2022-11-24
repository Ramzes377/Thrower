import asyncio
import re
from typing import TypeAlias

import aiohttp
import discord
import psycopg2
from discord.ext import commands
from asyncio_extras import async_contextmanager

from api.misc import get_category, flatten, query_identifiers

db_response_types: TypeAlias = int | float | str


class BaseCogMixin(commands.Cog):
    def __init__(self, bot):
        super(BaseCogMixin, self).__init__()
        self.bot = bot
        print(f'Cog {type(self).__name__} have been started!')


class ConnectionMixin:
    bot = None

    @async_contextmanager
    async def get_connection(self) -> None:
        try:
            async with self.bot.db.acquire() as conn:
                async with conn.cursor() as cur:
                    yield cur
        except psycopg2.OperationalError:
            await self.bot.db.clear()
            async with self.bot.db.acquire() as conn:
                async with conn.cursor() as cur:
                    yield cur

    @async_contextmanager
    async def url_request(self, url: str) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                yield response

    async def execute_sql(self, *scripts: str, fetch_all: bool = False) -> \
            list[tuple[db_response_types]] | list[db_response_types] | db_response_types:
        results = []
        async with self.get_connection() as cur:
            for script in scripts:
                many_identifiers = query_identifiers(script)
                await cur.execute(script)
                if fetch_all:
                    try:
                        result = await cur.fetchall()
                        if many_identifiers:
                            results.append(result)
                        else:
                            r = flatten(result)
                            results.extend(r) if r else results.append(r)
                    except Exception as e:
                        results.append(e)
                else:
                    try:
                        result = await cur.fetchone()
                        if len(scripts) > 1:
                            results.append(result if (many_identifiers or result is None) else result[0])
                        else:
                            results = result if (many_identifiers or result is None) else result[0]
                    except Exception as e:
                        results.append(e)
        return results


class DiscordFeaturesMixin(ConnectionMixin):
    async def get_user_channel(self, user_id: int) -> discord.VoiceChannel | None:
        channel_id: int = await self.execute_sql(f"SELECT channel_id FROM CreatedSessions WHERE user_id = {user_id}")
        return self.bot.get_channel(channel_id)

    async def get_user_sess_name(self, user: discord.member.Member) -> str:
        if user.activity and user.activity.type == discord.ActivityType.playing:
            sess_name = f"[{re.compile('[^a-zA-Z0-9а-яА-Я +]').sub('', user.activity.name)}]"
        else:
            have_default = await self.execute_sql(f'SELECT name FROM UserDefaultSessionName WHERE user_id = {user.id}')
            sess_name = have_default if have_default and have_default else f"{user.display_name}'s channel"
        return sess_name

    async def edit_channel_name_category(self, user: discord.member.Member, channel: discord.VoiceChannel, overwrites=None) -> None:
        channel_name = await self.get_user_sess_name(user)
        category = get_category(user)
        try:
            await asyncio.wait_for(channel.edit(name=channel_name, category=category, overwrites=overwrites), timeout=5.0)
        except asyncio.TimeoutError:  # Trying to rename channel in transfer but Discord restrictions :('
            await channel.edit(category=category)
