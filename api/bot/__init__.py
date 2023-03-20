from discord.ext import commands

from .cogs import (
    ChannelsManager,
    Commands,
    FloodManager,
    GameRoles,
    Logger,
    Music
)


async def setup(bot: commands.Bot):
    _cogs = [ChannelsManager, Commands, FloodManager, GameRoles, Logger]#, Music]
    for cog in _cogs:
        await bot.add_cog(cog(bot))
