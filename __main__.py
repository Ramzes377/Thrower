import warnings
from contextlib import suppress
from dataclasses import dataclass

import discord
from aiohttp import ClientConnectorError
from discord.ext import commands
from discord.ext.commands import ExtensionAlreadyLoaded

from api.service import init_configs
from config import Config
from utils import CustomWarning, clear_messages, logger

bot = commands.Bot(
    command_prefix='!',
    intents=discord.Intents.all(),
    fetch_offline_members=False,
)


@dataclass(frozen=True)
class Permissions:
    default = discord.PermissionOverwrite(
        kick_members=False,
        manage_channels=False,
        create_instant_invite=True
    )
    leader = discord.PermissionOverwrite(
        kick_members=True,
        manage_channels=True,
        create_instant_invite=True
    )


def _init_channels(bot: discord.Client) -> dataclass:
    @dataclass(frozen=True)
    class Channels:
        create: discord.VoiceChannel = bot.get_channel(Config.CREATE_CHANNEL_ID)
        logger: discord.VoiceChannel = bot.get_channel(Config.LOGGER_ID)
        request: discord.VoiceChannel = bot.get_channel(Config.ROLE_REQUEST_ID)
        commands: discord.VoiceChannel = bot.get_channel(Config.COMMAND_ID)

    return Channels


def _init_categories(bot: discord.Client) -> dict:
    return {
        None: bot.get_channel(Config.IDLE_CATEGORY_ID),
        discord.ActivityType.playing: bot.get_channel(Config.PLAYING_CATEGORY_ID)
    }


@bot.event
async def on_ready():

    await init_configs()

    bot.permissions = Permissions
    bot.channel = _init_channels(bot)
    bot.categories = _init_categories(bot)

    with suppress(ExtensionAlreadyLoaded):
        await bot.load_extension('bot')
    with suppress(ClientConnectorError):
        sync_commands = ', '.join(map(str, await bot.tree.sync()))

    await clear_messages(bot)

    logger.info("Bot have been started!")
    logger.info(f'Synced commands: {sync_commands}')


@bot.tree.error
async def on_command_error(_, error):
    warnings.warn(error, CustomWarning)


if __name__ == '__main__':
    bot.run(Config.TOKEN, reconnect=True)
