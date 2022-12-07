import discord
from discord.ext import commands
import lavalink

from api.bot.mixins import BaseCogMixin


class LavalinkVoiceClient(discord.VoiceClient):
    def __init__(self, client: discord.Client, channel: discord.abc.Connectable):
        self.client = client
        self.channel = channel

        if not hasattr(self.client, 'lavalink'):
            self.client.lavalink = lavalink.Client(client.user.id)
            self.client.lavalink.add_node('host.docker.internal', 2333, 'youshallnotpass', 'eu', 'default-node')
        self.lavalink = self.client.lavalink

    async def on_voice_server_update(self, data):
        data = {'t': 'VOICE_SERVER_UPDATE', 'd': data}
        await self.lavalink.voice_update_handler(data)

    async def on_voice_state_update(self, data):
        data = {'t': 'VOICE_STATE_UPDATE', 'd': data}
        await self.lavalink.voice_update_handler(data)

    async def connect(self, *, timeout: float, reconnect: bool, self_deaf: bool = False, self_mute: bool = False) -> None:
        self.lavalink.player_manager.create(guild_id=self.channel.guild.id)
        await self.channel.guild.change_voice_state(channel=self.channel, self_mute=self_mute, self_deaf=self_deaf)

    async def disconnect(self, *, force: bool = False) -> None:
        player = self.lavalink.player_manager.get(self.channel.guild.id)
        if not force and not player.is_connected:
            return
        await self.channel.guild.change_voice_state(channel=None)
        player.channel_id = None
        self.cleanup()


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


