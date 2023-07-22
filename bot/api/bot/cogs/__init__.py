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
class CogsContainer:
    channels_manager: Cog | Callable = ChannelsManager
    commands: Cog | Callable = Commands
    flood_manager: Cog | Callable = FloodManager
    game_roles: Cog | Callable = GameRoles
    logger: Cog | Callable = Logger
    music: Cog | Callable = Music
