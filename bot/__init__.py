import asyncio

from discord.ext import commands

from .cogs import cog

from config import Config


async def setup(bot: commands.Bot):
    await bot.add_cog(cog.commands(bot))

    if Config.MUSIC_ONLY:
        await bot.add_cog(cog.music(bot))
    else:
        await asyncio.gather(
            bot.add_cog(cog.channels_manager(bot)),
            bot.add_cog(cog.game_roles(bot)),
            bot.add_cog(cog.logger(bot))
        )
