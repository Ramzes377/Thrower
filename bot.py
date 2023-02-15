import asyncio
import os
import logging

import discord
from discord.ext import commands

from settings import envs, token, guild
from api.rest.base import request

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


@bot.event
async def on_ready():
    bot.create_channel = bot.get_channel(envs['create_channel_id'])
    bot.logger_channel = bot.get_channel(envs['logger_id'])
    bot.request_channel = bot.get_channel(envs['role_request_id'])
    bot.commands_channel = bot.get_channel(envs['command_id'])

    for category in categories:
        categories[category] = bot.get_channel(categories[category])

    await load_cogs(music_only=True, separate_load=True)
    await clear_unregistered_messages()
    print('Bot have been started!')


async def clear_unregistered_messages():
    guild = bot.guilds[0]
    text_channels = [channel for channel in guild.channels if channel.type.name == 'text']
    messages = await request('sent_message/')
    for message in messages:
        for channel in text_channels:
            try:
                msg = await channel.fetch_message(message['id'])
                if msg:
                    print(msg)
                    # deletion process
                    # await msg.delete()
                else:
                    print(await request(f'sent_message/{msg.id}', 'delete'))
            except:
                pass


async def load_cogs(music_only, separate_load=True):
    cogs_path = 'api/bot/cogs'
    cogs_path_dotted = cogs_path.replace('/', '.')
    if music_only:
        await bot.load_extension(f'{cogs_path_dotted}.music')
        await bot.load_extension(f'{cogs_path_dotted}.commands')
    else:
        for filename in reversed(os.listdir(cogs_path)):
            if filename.endswith('.py'):
                if filename != 'music.py':
                    await bot.load_extension(f'{cogs_path_dotted}.{filename[:-3]}')
                elif not separate_load:
                    await bot.load_extension(f'{cogs_path_dotted}.{filename[:-3]}')
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=" за каналами"))
    print(await bot.tree.sync(guild=guild))


run = lambda: bot.run(
    token,
    reconnect=True,
    log_handler=logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
)
