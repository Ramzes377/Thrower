import discord
import os
import aiopg
import asyncio

from discord.ext import commands
from api.cogs.tools.utils import categories, create_channel_id, logger_id, dsn, token, role_request_id
from api.cogs.tools.init_db import create_tables

try:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
except:
    pass

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, fetch_offline_members=False)
bot.db = None


@bot.event
async def on_ready():
    try:
        bot.db = await aiopg.create_pool(dsn)

        async with bot.db.acquire() as conn:
            async with conn.cursor() as cur:
                await create_tables(cur)

        await load_cogs()

        bot.create_channel = bot.get_channel(create_channel_id)
        bot.logger_channel = bot.get_channel(logger_id)
        bot.request_channel = bot.get_channel(role_request_id)
        for category in categories:
            categories[category] = bot.get_channel(categories[category])

        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=" за каналами"))
        await asyncio.ensure_future(clear_connections())
        print('Bot have been started!')
    except Exception as e:
        print('Error on startup: ', e)


async def clear_connections(period=60*5):
    while True:
        try:
            await bot.db.clear()
            await asyncio.sleep(period)
        except AttributeError:
            pass


async def load_cogs():
    for filename in reversed(os.listdir('api/cogs')):
        if filename.endswith('.py'):
            await bot.load_extension(f'api.cogs.{filename[:-3]}')


bot.run(token)
