from discord.ext import commands

from .cogs import CogContainer as cog

MUSIC_ONLY = False


async def setup(bot: commands.Bot):
    if MUSIC_ONLY:
        await bot.add_cog(cog.Music(bot))
    else:
        await bot.add_cog(cog.ChannelsManager(bot))
        await bot.add_cog(cog.Commands(bot))
        await bot.add_cog(cog.FloodManager(bot))
        await bot.add_cog(cog.GameRoles(bot))
        await bot.add_cog(cog.Logger(bot))
