import aiohttp
from discord.ext import commands
from asyncio_extras import async_contextmanager


class ConnectionMixin:
    bot = None

    @async_contextmanager
    async def get_connection(self):
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cur:
                yield cur

    @async_contextmanager
    async def url_request(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                yield response

    async def execute_sql(self, *scripts, fetch_all=False):
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

    async def get_user_channel(self, user_id):
        channel_id = await self.execute_sql(f"SELECT channel_id FROM CreatedSessions WHERE user_id = {user_id}")
        if channel_id:
            return self.bot.get_channel(*channel_id)


class BaseCog(commands.Cog, ConnectionMixin):
    def __init__(self, bot):
        self.bot = bot
        super(BaseCog, self).__init__()
        print(f'Cog {type(self).__name__} have been started!')