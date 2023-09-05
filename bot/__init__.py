from discord.ext import commands

from .cogs import CogsContainer as cog  # noqa

from config import Config


async def setup(bot: commands.Bot):
    await bot.add_cog(cog.commands(bot))

    if Config.MUSIC_ONLY:
        await bot.add_cog(cog.music(bot))
    else:
        await bot.add_cog(cog.channels_manager(bot))
        await bot.add_cog(cog.flood_manager(bot))
        await bot.add_cog(cog.game_roles(bot))
        await bot.add_cog(cog.logger(bot))
