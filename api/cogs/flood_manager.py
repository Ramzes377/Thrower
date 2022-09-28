import asyncio
from .tools.base_cog import BaseCog, commands
from .tools.utils import command_id, another_bots_prefixes, bots_ids


def message_belongs_bot(author_id):
    return any(author_id == id for id in bots_ids)


def user_calling_bot(msg_content):
    return msg_content.startswith(another_bots_prefixes)


async def remove_msg_after_delay(message, delay=30):
    await asyncio.sleep(delay)
    await message.delete()


class FloodManager(BaseCog):
    @commands.Cog.listener()
    async def on_message(self, message):
        author = message.author
        if author == self.bot.user or message.channel.id == command_id:
            return
        if user_calling_bot(message.content) or message_belongs_bot(author.id):
            await remove_msg_after_delay(message)


async def setup(bot):
    await bot.add_cog(FloodManager(bot))
