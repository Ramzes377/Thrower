import asyncio
import warnings
from contextlib import suppress
from dataclasses import dataclass

from aiohttp import ClientConnectorError
from discord import Intents, PermissionOverwrite
from discord.ext import commands

from src.config import Config
from src.app.service import Service
from src.utils import CustomWarning, _init_channels, _fill_activity_info, logger

bot = commands.Bot(
    command_prefix='!',
    intents=Intents.all(),
    fetch_offline_members=False,
)


@dataclass(frozen=True)
class Permissions:
    default = PermissionOverwrite(
        kick_members=False,
        manage_channels=False,
        create_instant_invite=True
    )
    leader = PermissionOverwrite(
        kick_members=True,
        manage_channels=True,
        create_instant_invite=True
    )


@bot.event
async def on_ready():
    asyncio.set_event_loop(bot.loop)
    asyncio.create_task(Service.deferrer.start(bot.loop))  # noqa

    bot.permissions = Permissions

    bot.guild_channels, *_ = await asyncio.gather(
        _init_channels(bot),
        _fill_activity_info(),
    )
    with suppress(commands.ExtensionAlreadyLoaded):
        await bot.load_extension('src.bot')  # load only after init data
    with suppress(ClientConnectorError):
        sync_commands = ', '.join(map(str, await bot.tree.sync()))

    logger.critical("Bot have been started!")
    logger.critical(f'Synced commands: {sync_commands}')


@bot.tree.error
async def on_command_error(_, error):
    warnings.warn(error, CustomWarning)
    logger.error(str(error))


def run_bot():
    with suppress(ClientConnectorError):
        bot.run(Config.token, reconnect=True)
