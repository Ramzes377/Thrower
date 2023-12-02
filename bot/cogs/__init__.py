from dataclasses import dataclass
from typing import Type

from discord.ext.commands import Cog

from config import Config

from bot.cogs.channels_manager import ChannelsManager
from bot.cogs.commands import Commands
from bot.cogs.gameroles import GameRoles
from bot.cogs.logger import Logger


@dataclass
class CogsContainer:
    channels_manager: Type[Cog]
    commands: Type[Cog]
    game_roles: Type[Cog]
    logger: Type[Cog]
    music: Type[Cog] = None


cog = CogsContainer(
    channels_manager=ChannelsManager,
    commands=Commands,
    game_roles=GameRoles,
    logger=Logger,
)

if Config.music_only:
    from bot.cogs.music import Music

    cog.music = Music
