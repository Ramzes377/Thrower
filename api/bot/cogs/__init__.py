from dataclasses import dataclass
from typing import Callable

from discord.ext.commands import Cog

from .channels_manager import ChannelsManager
from .commands import Commands
from .flood_manager import FloodManager
from .gameroles import GameRoles
from .logger import Logger
from .music import Music


@dataclass(frozen=True)
class CogContainer:
    ChannelsManager: Cog | Callable = ChannelsManager
    Commands: Cog | Callable = Commands
    FloodManager: Cog | Callable = FloodManager
    GameRoles: Cog | Callable = GameRoles
    Logger: Cog | Callable = Logger
    Music: Cog | Callable = Music
