import asyncio
import os

import discord
from discord.ext import commands

from api.bot.vars import set_vars, token

try:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
except:
    pass

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, fetch_offline_members=False)
bot.db = None


async def clear_unregistered_messages(bot):
    guild = bot.guilds[0]
    exclude = [bot.logger_channel, bot.request_channel]
    pub_text_channels = (channel for channel in guild.channels if
                         channel.type.name == 'text' and channel not in exclude)
    for channel in pub_text_channels:
        deleted = await channel.purge(limit=100, check=lambda msg: msg.author == bot.user)
        n = len(deleted)
        if n > 0:
            print(f'Delete {len(deleted)} messages from {channel}!')


@bot.event
async def on_ready():
    set_vars(bot)
    await load_cogs(music=True)
    await clear_unregistered_messages(bot)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=" за каналами"))
    print('Bot have been started!')


@bot.tree.error
async def on_command_error(ctx, error):
    print(ctx, error)
    pass


async def load_cogs(music=False):
    cogs_path = 'api/bot/cogs'
    cogs_path_dotted = cogs_path.replace('/', '.')
    exclude = ['music.py']
    if music:
        await bot.load_extension(f'{cogs_path_dotted}.music')
    else:
        for filename in reversed(os.listdir(cogs_path)):
            if filename.endswith('.py') and filename.lower() not in exclude:
                await bot.load_extension(f'{cogs_path_dotted}.{filename[:-3]}')


bot.run(token)
