from dataclasses import dataclass
from typing import Type

from discord.ext.commands import Cog

from src.config import Config

from src.bot.cogs.channels_manager import ChannelsManager
from src.bot.cogs.commands import Commands
from src.bot.cogs.gameroles import GameRoles
from src.bot.cogs.logger.logger import Logger


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
    from src.bot.cogs.music.music import Music

    cog.music = Music
