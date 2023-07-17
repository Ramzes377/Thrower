import warnings
from contextlib import suppress

import discord
from aiohttp import ClientConnectorError
from discord.ext import commands
from discord.ext.commands import ExtensionAlreadyLoaded

from settings import (
    token, Permissions,
    _init_channels,
    _init_categories,
    clear_unregistered_messages, CustomWarning, logger
)

bot = commands.Bot(
    command_prefix='!',
    intents=discord.Intents.all(),
    fetch_offline_members=False,
)


@bot.event
async def on_ready():
    bot.permissions = Permissions
    bot.channel = _init_channels(bot)
    bot.categories = _init_categories(bot)

    with suppress(ExtensionAlreadyLoaded):
        await bot.load_extension('api.bot')
    with suppress(ClientConnectorError):
        await bot.tree.sync()

    await clear_unregistered_messages(bot)

    #warnings.warn("Bot have been started!", CustomWarning)
    logger.info("Bot have been started!")


@bot.tree.error
async def on_command_error(ctx, error):
    warnings.warn(error, CustomWarning)


def run():
    bot.run(token, reconnect=True)
