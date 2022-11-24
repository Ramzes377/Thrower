import discord
import lavalink
from discord.ext import commands

from api.core.music.voiceclient import LavalinkVoiceClient
from api.mixins import BaseCogMixin


class MusicBase(BaseCogMixin):
    def __init__(self, bot):
        super(MusicBase, self).__init__(bot)
        if not hasattr(bot, 'lavalink'):  # This ensures the client isn't overwritten during cog reloads.
            bot.lavalink = lavalink.Client(bot.user.id)
            bot.lavalink.add_node('host.docker.internal', 2333, 'youshallnotpass', 'eu', 'default-node')

    async def cog_before_invoke(self, ctx):
        """ Command before-invoke handler. """
        guild_check = ctx.guild is not None
        if guild_check:
            await self.ensure_voice(ctx)
        return guild_check

    async def cog_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        if isinstance(error, commands.CommandInvokeError):
            await interaction.response.send_message(error.original, delete_after=60)

    async def ensure_voice(self, ctx):
        """ This check ensures that the bot and command author are in the same voicechannel. """

        try:
            await ctx.message.delete(delay=5)
        except:
            pass

        player = self.bot.lavalink.player_manager.create(ctx.guild.id)

        if not ctx.author.voice or not ctx.author.voice.channel:
            raise discord.app_commands.AppCommandError('Join a voicechannel first.')

        need_vc = ctx.command.name not in ('favorite', 'queue', 'sync')
        if not need_vc:
            return

        v_client = ctx.voice_client
        if not v_client:
            player.store('channel', ctx.channel.id)
            try:
                await ctx.author.voice.channel.connect(cls=LavalinkVoiceClient)
            except discord.errors.ClientException:
                pass
        elif v_client.channel.id != ctx.author.voice.channel.id:
            raise discord.app_commands.AppCommandError('You need to be in my voicechannel.')

