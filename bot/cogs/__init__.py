from dataclasses import dataclass
from typing import Callable

from discord.ext.commands import Cog

from config import Config

from bot.cogs.channels_manager import ChannelsManager
from bot.cogs.commands import Commands
from bot.cogs.flood_manager import FloodManager
from bot.cogs.gameroles import GameRoles
from bot.cogs.logger import Logger


@dataclass(frozen=True)
class CogsContainer:
    channels_manager: Cog | Callable = ChannelsManager
    commands: Cog | Callable = Commands
    flood_manager: Cog | Callable = FloodManager
    game_roles: Cog | Callable = GameRoles
    logger: Cog | Callable = Logger
    music: Cog | Callable = None

    def __post_init__(self):
        if Config.MUSIC_ONLY:
            from .music import Music
            self.music = Music      # noqa
