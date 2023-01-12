import asyncio
import os

import discord
from discord.ext import commands

from settings import envs, token

try:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
except:
    pass

categories = {
    None: envs['idle_category_id'],
    discord.ActivityType.playing: envs['playing_category_id']
}

leader_role_perms = discord.PermissionOverwrite(
    kick_members=True,
    manage_channels=True,
    create_instant_invite=True
)

default_role_perms = discord.PermissionOverwrite(
    kick_members=False,
    manage_channels=False,
    create_instant_invite=True
)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, fetch_offline_members=False)
bot.logger_channel, bot.request_channel = None, None


@bot.event
async def on_ready():
    bot.create_channel = bot.get_channel(envs['create_channel_id'])
    bot.logger_channel = bot.get_channel(envs['logger_id'])
    bot.request_channel = bot.get_channel(envs['role_request_id'])
    bot.commands_channel = bot.get_channel(envs['command_id'])

    for category in categories:
        categories[category] = bot.get_channel(categories[category])

    await load_cogs(music=False)
    await clear_unregistered_messages()
    await bot.tree.sync(guild=discord.Object(id=envs['guild_id']))
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=" за каналами"))
    print('Bot have been started!')


@bot.tree.error
async def on_command_error(ctx, error):
    print(ctx, error)
    pass


async def clear_unregistered_messages():
    guild = bot.guilds[0]
    exclude = [bot.logger_channel, bot.request_channel]

    if any(not channel for channel in exclude):
        raise ValueError('Dangerous behavior! Check exclude channels.')

    pub_text_channels = (channel for channel in guild.channels if
                         channel.type.name == 'text' and channel not in exclude)
    for channel in pub_text_channels:
        deleted = await channel.purge(limit=100, check=lambda msg: msg.author == bot.user)
        n = len(deleted)
        if n > 0:
            print(f'Delete {len(deleted)} messages from {channel}!')


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


run = lambda: bot.run(token)
