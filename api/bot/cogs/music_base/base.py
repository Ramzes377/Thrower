import lavalink
import discord
from discord import app_commands

from api.bot.mixins import DiscordFeaturesMixin

not_connected = discord.app_commands.AppCommandError('Сначала войдите в голосовой канал!')
not_same_voicechat = discord.app_commands.AppCommandError('Вы должны быть в том же голосовом чате!')


class LavalinkVoiceClient(discord.VoiceClient):
    def __init__(self, client: discord.Client, channel: discord.abc.Connectable):
        super().__init__(client, channel)
        self.lavalink = self.client.lavalink

    async def on_voice_server_update(self, data):
        data = {'t': 'VOICE_SERVER_UPDATE', 'd': data}
        await self.lavalink.voice_update_handler(data)

    async def on_voice_state_update(self, data):
        data = {'t': 'VOICE_STATE_UPDATE', 'd': data}
        await self.lavalink.voice_update_handler(data)

    async def connect(self, *, timeout: float, reconnect: bool, self_deaf: bool = False,
                      self_mute: bool = False) -> None:
        self.lavalink.player_manager.create(guild_id=self.channel.guild.id)
        await self.channel.guild.change_voice_state(channel=self.channel, self_mute=self_mute, self_deaf=self_deaf)

    async def disconnect(self, *, force: bool = False) -> None:
        player = self.lavalink.player_manager.get(self.channel.guild.id)
        if not force and not player.is_connected:
            return
        await self.channel.guild.change_voice_state(channel=None)
        player.channel_id = None
        self.cleanup()


class MusicBase(DiscordFeaturesMixin):
    view = None

    def __init__(self, bot):
        super(MusicBase, self).__init__(bot)
        lavalink.add_event_hook(self.events_handler)
        if not hasattr(bot, 'lavalink'):  # This ensures the client isn't overwritten during cog reloads.
            bot.lavalink = lavalink.Client(bot.user.id)
            bot.lavalink.add_node('host.docker.internal', 2333,
                                  'youshallnotpass', 'eu', 'default-node',
                                  10, 'Client', 30)

    async def events_handler(self, event: lavalink.events.Event):
        if isinstance(event, lavalink.events.NodeConnectedEvent):
            await self.bot.change_presence(
                activity=discord.Activity(type=discord.ActivityType.watching, name=" за заказами 🎶"))
            print('Ready to accept orders . . .')

        if isinstance(event, lavalink.events.QueueEndEvent):
            player = event.player
            guild = self.bot.get_guild(player.guild_id)

            try:
                await self.clear_player_message(player)
                await guild.voice_client.disconnect(force=True)
            finally:
                pass

        if isinstance(event, lavalink.events.TrackStartEvent):
            await self.update_msg(event.player)

    async def cog_before_invoke(self, ctx):
        """ Command before-invoke handler. """
        guild_check = ctx.guild is not None
        if guild_check:
            await self.ensure_voice(ctx)
        return guild_check

    async def cog_app_command_error(self, interaction: discord.Interaction,
                                    error: discord.app_commands.AppCommandError):
        if isinstance(error, discord.app_commands.AppCommandError):
            try:
                await interaction.response.send_message(error, delete_after=15, ephemeral=True)
            except discord.errors.InteractionResponded:
                pass

    async def ensure_voice(self, ctx):
        """ This check ensures that the bot and command author are in the same voicechannel. """
        player = self.bot.lavalink.player_manager.create(ctx.guild.id)

        if not ctx.author.voice or not ctx.author.voice.channel:
            raise not_connected

        need_vc = ctx.command.name not in ('favorite', 'queue', 'sync')
        if not need_vc:
            return

        v_client = ctx.voice_client
        if not v_client:
            player.store('channel', ctx.guild.get_channel(ctx.channel.id))
            await ctx.author.voice.channel.connect(cls=LavalinkVoiceClient)
        elif v_client.channel.id != ctx.author.voice.channel.id:
            raise not_same_voicechat

    async def update_msg(self, player: lavalink.DefaultPlayer) -> None:
        """Creates a player UI bar"""

        if not player.current:
            return

        current_track = player.current.title
        thumbnail_url = f"http://i3.ytimg.com/vi/{player.current.identifier}/maxresdefault.jpg"
        requester = f'<@{player.current.requester}>'
        status = ':musical_note: Играет :musical_note:' if not player.paused else ':pause_button: Пауза :pause_button:'

        message = player.fetch('message')
        if message:
            # when we calling it and message already exists then we expect to change ONLY current track or playing status
            embed = message.embeds[0]
            embed.set_field_at(0, name='Текущий трек', value=current_track)
            embed.set_field_at(1, name='Статус', value=status, inline=False)
            embed.set_field_at(2, name='Поставил', value=requester, inline=False)
            embed.set_thumbnail(url=thumbnail_url)
            try:
                await message.edit(embed=embed)
            except discord.errors.NotFound:  # message were deleted for some reason, just recreate it
                await self.clear_player_message(player)
            return

        embed = (discord.Embed(color=discord.Color.blurple())
                 .add_field(name='Текущий трек', value=current_track)
                 .add_field(name='Статус', value=status, inline=False)
                 .add_field(name='Поставил', value=requester, inline=False)
                 .set_thumbnail(url=thumbnail_url)
                 .set_footer(text=f'Великий бот - {self.bot.user.display_name}', icon_url=self.bot.user.avatar))

        channel = player.fetch('channel') or self.bot.commands_channel
        message = await self.log_message(channel.send(embed=embed, view=self.view))
        player.store('message', message)

    async def clear_player_message(self, player: lavalink.DefaultPlayer):
        try:
            message = player.fetch('message')
            await message.delete()
        except AttributeError:
            pass
        finally:
            player.store('message', None)
