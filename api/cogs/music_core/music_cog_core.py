import lavalink
from discord.ext import commands

from api.cogs.music_core.lavalink_vc import LavalinkVoiceClient
from api.cogs.tools.mixins import BaseCogMixin


class MusicCore(BaseCogMixin):
    update_msg = lambda: None

    def __init__(self, bot):
        super(MusicCore, self).__init__(bot)
        if not hasattr(bot, 'lavalink'):  # This ensures the client isn't overwritten during cog reloads.
            bot.lavalink = lavalink.Client(bot.user.id)
            bot.lavalink.add_node('127.0.0.1', 2333, 'youshallnotpass', 'eu', 'default-node')
        lavalink.add_event_hook(self.track_hook)

    async def cog_before_invoke(self, ctx):
        """ Command before-invoke handler. """
        guild_check = ctx.guild is not None
        if guild_check:
            await self.ensure_voice(ctx)
        return guild_check

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(error.original, delete_after=60)

    async def ensure_voice(self, ctx):
        """ This check ensures that the bot and command author are in the same voicechannel. """

        try:
            await ctx.message.delete(delay=5)
        except:
            pass

        player = self.bot.lavalink.player_manager.create(ctx.guild.id)

        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandInvokeError('Join a voicechannel first.')

        need_vc = ctx.command.name not in ('preferences', )
        if not need_vc:
            return

        v_client = ctx.voice_client
        if not v_client:
            # permissions = ctx.author.voice.channel.permissions_for(ctx.me)
            #
            # if not permissions.connect or not permissions.speak:  # Check user limit too?
            #     raise commands.CommandInvokeError('I need the `CONNECT` and `SPEAK` permissions.')

            player.store('channel', ctx.channel.id)
            await ctx.author.voice.channel.connect(cls=LavalinkVoiceClient)
        elif v_client.channel.id != ctx.author.voice.channel.id:
            raise commands.CommandInvokeError('You need to be in my voicechannel.')

    async def track_hook(self, event):
        if isinstance(event, lavalink.events.QueueEndEvent):
            guild_id = event.player.guild_id
            guild = self.bot.get_guild(guild_id)

            try:
                await self._msg.delete()
                self._msg = None
            except:
                pass

            await guild.voice_client.disconnect(force=True)
        if isinstance(event, lavalink.events.TrackStartEvent):
            await self.update_msg()
