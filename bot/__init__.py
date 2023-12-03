import asyncio
from contextlib import suppress
from typing import TYPE_CHECKING

from discord.ext.commands import ExtensionAlreadyLoaded

from bot.cogs import cog
from config import Config

if TYPE_CHECKING:
    from discord.ext.commands import Bot


async def setup(bot: "Bot"):
    with suppress(ExtensionAlreadyLoaded):
        await bot.add_cog(cog.commands(bot))

        if Config.music_only:
            await bot.add_cog(cog.music(bot))
        else:
            await asyncio.gather(
                bot.add_cog(cog.channels_manager(bot)),
                bot.add_cog(cog.game_roles(bot)),
                bot.add_cog(cog.logger(bot))
            )
