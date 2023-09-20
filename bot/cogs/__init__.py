from dataclasses import dataclass

from discord.ext.commands import Cog

from config import Config

from bot.cogs.channels_manager import ChannelsManager
from bot.cogs.commands import Commands
from bot.cogs.flood_manager import FloodManager
from bot.cogs.gameroles import GameRoles
from bot.cogs.logger import Logger


@dataclass
class CogsContainer:
    channels_manager: Cog
    commands: Cog
    flood_manager: Cog
    game_roles: Cog
    logger: Cog
    music: Cog = None


cog = CogsContainer(
    channels_manager=ChannelsManager,
    commands=Commands,
    flood_manager=FloodManager,
    game_roles=GameRoles,
    logger=Logger,
)

if Config.MUSIC_ONLY:

    from bot.cogs.music import Music

    cog.music = Music
