import asyncio

import discord

from api.mixins import BaseCogMixin, commands
from api.misc import command_id, another_bots_prefixes, bots_ids


def message_belongs_bot(author_id: int) -> bool:
    return any(author_id == id for id in bots_ids)


def user_calling_bot(content: str) -> bool:
    return content.startswith(another_bots_prefixes)


class FloodManager(BaseCogMixin):
    REMOVE_DELAY = 30   # in seconds

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        author = message.author
        if author == self.bot.user or message.channel.id == command_id:
            return
        if user_calling_bot(message.content) or message_belongs_bot(author.id):
            await asyncio.sleep(FloodManager.REMOVE_DELAY)
            await message.delete()


async def setup(bot):
    await bot.add_cog(FloodManager(bot))
