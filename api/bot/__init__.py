from discord.ext import commands

from .cogs import CogContainer as cog


async def setup(bot: commands.Bot):
    # await bot.add_cog(cog.ChannelsManager(bot))
    # await bot.add_cog(cog.Commands(bot))
    # await bot.add_cog(cog.FloodManager(bot))
    # await bot.add_cog(cog.GameRoles(bot))
    # await bot.add_cog(cog.Logger(bot))
    await bot.add_cog(cog.Music(bot))

