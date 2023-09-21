import asyncio
import re
from contextlib import suppress

import discord
import lavalink

from config import Config
from utils import logger
from bot.mixins import DiscordFeaturesMixin
from .views import PlayerButtonsView
from .views import create_view

url_rx = re.compile(r'https?://(?:www\.)?.+')

not_connected = discord.app_commands.AppCommandError(
    'Сначала войдите в голосовой канал!'
)
not_same_voicechat = discord.app_commands.AppCommandError(
    'Вы должны быть в том же голосовом чате!'
)


def code(func):
    def wrapper(*args, **kwargs) -> str:
        wrap = '```'
        result = func(*args, **kwargs)
        return f'{wrap}{result}{wrap}'

    return wrapper


class LavalinkVoiceClient(discord.VoiceClient):
    def __init__(
        self,
        client: discord.Client,
        channel: discord.abc.Connectable
    ):
        super().__init__(client, channel)
        self.lavalink = self.client.lavalink

    async def on_voice_server_update(self, data):
        data = {'t': 'VOICE_SERVER_UPDATE', 'd': data}
        await self.lavalink.voice_update_handler(data)

    async def on_voice_state_update(self, data):
        data = {'t': 'VOICE_STATE_UPDATE', 'd': data}
        await self.lavalink.voice_update_handler(data)

    async def connect(
        self,
        *,
        timeout: float,
        reconnect: bool,
        self_deaf: bool = False,
        self_mute: bool = False
    ) -> None:
        self.lavalink.player_manager.create(guild_id=self.channel.guild.id)
        await self.channel.guild.change_voice_state(
            channel=self.channel,
            self_mute=self_mute,
            self_deaf=self_deaf
        )

    async def disconnect(self, *, force: bool = False) -> None:
        player = self.lavalink.player_manager.get(self.channel.guild.id)
        if not force and not player.is_connected:
            return
        await self.channel.guild.change_voice_state(channel=None)
        player.channel_id = None
        self.cleanup()


class MusicBase(DiscordFeaturesMixin):
    view = None
    params = dict(
        name='Client',
        region='eu',
        host=Config.LAVALINK_URI,
        port=Config.LAVALINK_PORT,
        password=Config.LAVALINK_PASSWORD,
        resume_key='default-node',
        resume_timeout=10,
        reconnect_attempts=30
    )

    def __init__(self, bot):
        super(MusicBase, self).__init__(bot)
        if not hasattr(bot, 'lavalink'):
            # This ensures the client isn't overwritten during cog reloads.
            bot.lavalink = lavalink.Client(bot.user.id)
            bot.lavalink.add_node(**self.params)

        lavalink.add_event_hook(self.events_handler)

    async def events_handler(self, event: lavalink.events.Event):

        match type(event):

            case lavalink.events.NodeConnectedEvent:

                await self.bot.change_presence(
                    activity=discord.Activity(
                        type=discord.ActivityType.watching,
                        name=" за заказами 🎶"
                    )
                )
                logger.info("Ready to accept orders . . .")

            case lavalink.events.QueueEndEvent:

                player = event.player
                guild = self.bot.get_guild(player.guild_id)

                await self.clear_player_message(player)

                with suppress(AttributeError):
                    await asyncio.sleep(3 * 60)  # wait 3 minutes and leave
                    # if queue is empty

                    u = self.bot.lavalink.player_manager.get(player.guild_id)
                    if not u.current:
                        await guild.voice_client.disconnect(force=True)

            case lavalink.events.TrackStartEvent:

                await self.update_msg(event.player)

    async def cog_before_invoke(self, ctx):
        """ Command before-invoke handler. """
        if guild_check := (ctx.guild is not None):
            await self.ensure_voice(ctx)
        return guild_check

    async def cog_app_command_error(
        self, interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError
    ):
        with suppress(discord.InteractionResponded, discord.NotFound):
            await interaction.response.send_message(  # noqa
                error,
                delete_after=15,
                ephemeral=True,
            )

    async def ensure_voice(self, ctx):
        """ This check ensures that the bot and
        command author are in the same voice channel. """

        player = self.bot.lavalink.player_manager.create(ctx.guild.id)

        if not ctx.author.voice or not ctx.author.voice.channel:
            raise not_connected

        need_vc = ctx.command.name not in ('favorite', 'queue', 'sync')
        if not need_vc:
            return

        v_client = ctx.voice_client
        if not v_client:
            with suppress(discord.errors.ClientException):
                player.store('channel', ctx.guild.get_channel(ctx.channel.id))
                await ctx.author.voice.channel.connect(cls=LavalinkVoiceClient)
        elif v_client.channel.id != ctx.author.voice.channel.id:
            raise not_same_voicechat

    async def update_msg(self, player: lavalink.BasePlayer) -> None:
        """Creates a player UI bar"""

        if not player.current:
            return

        current_track = player.current.title
        thumbnail_url = f"http://i3.ytimg.com/vi/{player.current.identifier}/maxresdefault.jpg"
        requester = f'<@{player.current.requester}>'
        status = ':musical_note:' if not player.paused else ':pause_button:'

        message = player.fetch('message')
        if message:
            # when we calling it and message already exists then we
            # expect to change ONLY current track or playing status
            embed = message.embeds[0]
            embed.set_field_at(0, name='Текущий трек', value=current_track)
            embed.set_field_at(1, name='Статус', value=status, inline=False)
            embed.set_field_at(2, name='Поставил', value=requester,
                               inline=False)
            embed.set_thumbnail(url=thumbnail_url)
            try:
                await message.edit(embed=embed)
            except discord.errors.NotFound:
                # message were deleted for source reason, just recreate it
                await self.clear_player_message(player)
            return

        embed = (
            discord.Embed(color=discord.Color.blurple())
            .add_field(name='Текущий трек', value=current_track)
            .add_field(name='Статус', value=status, inline=False)
            .add_field(name='Поставил', value=requester, inline=False)
            .set_thumbnail(url=thumbnail_url)
        )

        channel = player.fetch('channel') or self.bot.channel.commands
        message = await self.log_message(
            channel.send(embed=embed, view=self.view)
        )
        player.store('message', message)

    @staticmethod
    async def clear_player_message(player: lavalink.BasePlayer):
        with suppress(AttributeError):
            message = player.fetch('message')
            await message.delete()
        player.store('message', None)

    async def _get_context(
        self, interaction: discord.Interaction,
        command_name: str):
        try:
            ctx = await self.bot.get_context(interaction)
        except ValueError:
            guild = self.bot.get_guild(interaction.guild_id)
            command = type('Command', tuple(), {'name': command_name})
            ctx = type(
                'Context',
                tuple(),
                {
                    'guild': guild,
                    'author': guild.get_member(interaction.user.id),
                    'command': command, 'voice_client': None,
                    'channel': interaction.channel,
                    'me': interaction.client.user
                }
            )
        return ctx


@code
def queue_repr(queue: list, current: str) -> str:
    others = '\n'.join(
        (f"{i:3}. {x.title}" for i, x in enumerate(queue[:9], start=2)))
    result = f'{1:3}. {current}\n{others}'
    remains = len(queue) - 9
    ending = '' if remains < 0 else f'\nи еще ({remains}) ...'
    return f'{result}{ending}'


class MusicCommandsHandlers(MusicBase):
    def __init__(self, bot):
        super().__init__(bot)
        self.view = PlayerButtonsView(self._pause, self._skip,
                                      self._queue, self._favorite)

    async def _get_embed(
        self,
        user_id: int,
        results: lavalink.models.LoadResult,
        player: lavalink.DefaultPlayer,
        query: str
    ) -> discord.Embed:

        embed = discord.Embed(color=discord.Color.blurple())
        if results.load_type == 'PLAYLIST_LOADED':
            tracks = results.tracks
            for track in tracks:
                player.add(requester=user_id, track=track)
            embed.title = 'Плейлист добавлен в очередь!'
            embed.description = f'{results.playlist_info.name} - {len(tracks)} tracks'
            data = {'title': results.playlist_info.name, 'query': query,
                    'user_id': user_id, 'counter': 1}
        else:
            track = results.tracks[0]
            embed.title = 'Трек добавлен в очередь!'
            embed.description = f'[{track.title}]({track.uri})'
            player.add(requester=user_id, track=track)
            data = {'title': track.title, 'query': track.uri,
                    'user_id': user_id, 'counter': 1}

        await self.db.music_create(data)
        return embed

    async def _play(self, interaction: discord.Interaction, query: str) -> None:
        """ Searches and plays a song from a given query. """
        ctx = await self._get_context(interaction, command_name='play')
        await self.ensure_voice(ctx)

        player = self.bot.lavalink.player_manager.get(interaction.guild_id)
        query = query.strip('<>')
        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        results = await player.node.get_tracks(query)

        if not results or not results.tracks:
            raise discord.app_commands.AppCommandError('Ничего не найдено!')

        embed = await self._get_embed(interaction.user.id, results, player,
                                      query)

        try:
            msg = await interaction.response.send_message(  # noqa
                embed=embed,
                ephemeral=False,
                delete_after=30
            )
            await self.db.create_sent_message(msg.id)
        except discord.InteractionResponded:
            msg = await interaction.followup.send(  # noqa
                embed=embed,
                ephemeral=False
            )
            await self.db.create_sent_message(msg.id)
        except AttributeError:
            pass

        if not player.is_playing:
            await player.play()

    async def _stop(self, interaction: discord.Interaction) -> None:
        """ Disconnects the player from the voice channel and clears its queue. """
        ctx = await self.bot.get_context(interaction)
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not ctx.voice_client:
            raise not_connected

        if not ctx.author.voice or (
                player.is_connected and ctx.author.voice.channel.id != int(
            player.channel_id)):
            raise not_same_voicechat

        player.queue.clear()

        try:
            await self.clear_player_message(player)
        finally:
            await player.stop()
            await ctx.voice_client.disconnect(force=True)
            msg = 'Принудительно завершено исполнение!'
            await self.log_message(
                interaction.response.send_message(  # noqa
                    msg,
                    ephemeral=False,
                    delete_after=30
                )
            )

    async def _queue(self, interaction: discord.Interaction) -> None:
        ctx = await self._get_context(interaction, command_name='queue')

        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if player is None or (not player.is_playing and not player.queue):
            raise discord.app_commands.AppCommandError('Очередь пуста!')

        queue_msg = queue_repr(player.queue, player.current.title)
        await self.log_message(
            interaction.response.send_message(  # noqa
                queue_msg,
                ephemeral=False,
                delete_after=30
            )
        )

    async def _favorite(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            'Список избранных треков отправлен в ЛС',
            ephemeral=True, delete_after=10)
        user = interaction.user
        favorites = await self.db.get_user_favorite_music(user.id)
        try:
            view = create_view('Выберите трек для добавления в очередь',
                               favorites,
                               interaction.guild_id, handler=self._play)
            await self.log_message(user.send(view=view, delete_after=60))
        except AttributeError:
            await self.log_message(
                user.send(
                    'У вас нет избранных треков. '
                    'Возможно, вы не ставили никаких треков.',
                    delete_after=60
                )
            )

    async def _pause(self, interaction: discord.Interaction) -> None:
        player = self.bot.lavalink.player_manager.get(interaction.guild_id)
        player.paused = not player.paused
        status = "приостановлено" if player.paused else "вознобновлено"
        with suppress(AttributeError):
            msg = f'Воспроизведение {status}! \n' \
                  f'Пользователь: {interaction.user.mention}'
            await self.log_message(
                interaction.response.send_message(  # noqa
                    msg,
                    ephemeral=False,
                    delete_after=15
                )
            )
        await player.set_pause(player.paused)
        await self.update_msg(player)

    async def _skip(self, interaction: discord.Interaction) -> None:
        player = self.bot.lavalink.player_manager.get(interaction.guild_id)
        with suppress(AttributeError):
            msg = f'Пропущено воспроизведение трека {player.current.title}! \n' \
                  f'Пользователь: {interaction.user.mention}'
            await self.log_message(
                interaction.response.send_message(  # noqa
                    msg,
                    ephemeral=False,
                    delete_after=15
                )
            )
        await player.skip()
        await self.update_msg(player)
