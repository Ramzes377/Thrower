import discord

from ..mixins import BaseCogMixin, commands
from settings import bots_ids, envs


def message_belongs_bot(author_id: int) -> bool:
    return any(author_id == bot_id for bot_id in bots_ids)


def user_calling_bot(content: str) -> bool:
    return content.startswith('/')


class FloodManager(BaseCogMixin):
    REMOVE_DELAY = 30   # in seconds

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        author = message.author
        if author == self.bot.user or message.channel.id == envs['command_id']:
            return
        if user_calling_bot(message.content) or message_belongs_bot(author.id):
            await message.delete(delay=FloodManager.REMOVE_DELAY)


async def setup(bot):
    await bot.add_cog(FloodManager(bot))
