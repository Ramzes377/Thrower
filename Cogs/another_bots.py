from .base_COG import *

command_id = int(os.environ.get('Command_channel_ID'))

BOTS_IDS = [184405311681986560, 721772274830540833]
another_bots_prefixes = [';;', '-v']

class Message_manager(Base_COG):

    @commands.Cog.listener()
    async def on_message(self, message):
        author = message.author
        if author == self.bot.user or message.channel.id == command_id:
            return

        if self.user_calling_bot(message.content) or self.message_belongs_bot(author.id):
            await self.remove_msg_after_delay(message)

    def message_belongs_bot(self, author_id):
        return any(author_id == id for id in BOTS_IDS)

    def user_calling_bot(self, msg_content):
        return any(msg_content.startswith(prefix) for prefix in another_bots_prefixes)

    async def remove_msg_after_delay(self, message, delay = 30):
        await asyncio.sleep(delay)
        await message.delete()



def setup(bot):
    bot.add_cog(Message_manager(bot))
