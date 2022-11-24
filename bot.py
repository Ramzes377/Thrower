import asyncio
import os

import discord
import aiopg

from discord.ext import commands
from api.tools.misc import categories, create_channel_id, logger_id, dsn, token, role_request_id, command_id
from api.tools.init_db import create_tables

try:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
except:
    pass

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, fetch_offline_members=False)
bot.db = None


async def clear_unregistered_messages_on_startup(bot):
    guild = bot.guilds[0]
    exclude = [bot.logger_channel, bot.request_channel]
    pub_text_channels = (channel for channel in guild.channels if
                         channel.type.name == 'text' and channel not in exclude)
    for channel in pub_text_channels:
        deleted = await channel.purge(limit=100, check=lambda msg: msg.author == bot.user)
        print(f'Delete {len(deleted)} messages from {channel}!')


@bot.event
async def on_ready():
    try:
        bot.db = await aiopg.create_pool(dsn)

        async with bot.db.acquire() as conn:
            async with conn.cursor() as cur:
                await create_tables(cur)

        bot.create_channel = bot.get_channel(create_channel_id)
        bot.logger_channel = bot.get_channel(logger_id)
        bot.request_channel = bot.get_channel(role_request_id)
        bot.commands_channel = bot.get_channel(command_id)

        for category in categories:
            categories[category] = bot.get_channel(categories[category])

        await load_cogs()
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=" за каналами"))
        print('Bot have been started!')
    except Exception as e:
        print('Error on startup: ', e)


@bot.tree.error
async def on_command_error(ctx, error):
    pass


async def load_cogs():
    for filename in reversed(os.listdir('cogs')):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')


bot.run(token)
bot.loop.create_task(clear_unregistered_messages_on_startup(bot))
