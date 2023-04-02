from discord.ext import commands

from settings import MUSIC_ONLY
from .cogs import CogsContainer as cogs


async def setup(bot: commands.Bot):

    await bot.add_cog(cogs.Commands(bot))

    if MUSIC_ONLY:
        await bot.add_cog(cogs.Music(bot))
    else:
        await bot.add_cog(cogs.ChannelsManager(bot))
        await bot.add_cog(cogs.FloodManager(bot))
        await bot.add_cog(cogs.GameRoles(bot))
        await bot.add_cog(cogs.Logger(bot))
