import discord

from api.bot.mixins import BaseCogMixin, commands
from api.bot.vars import bots_ids, another_bots_prefixes, command_id


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
            await message.delete(delay=FloodManager.REMOVE_DELAY)


async def setup(bot):
    await bot.add_cog(FloodManager(bot))
