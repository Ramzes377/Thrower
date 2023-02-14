import re

import lavalink
import discord
from discord import app_commands
from discord.ext import commands

from settings import envs
from .music_base import MusicBase, create_view, not_connected, not_same_voicechat, PlayerButtonsView
from ..misc import code

url_rx = re.compile(r'https?://(?:www\.)?.+')


@code
def queue_repr(queue: list, current: str) -> str:
    others = '\n'.join((f"{i:3}. {x.title}" for i, x in enumerate(queue[:9], start=2)))
    result = f'{1:3}. {current}\n{others}'
    remains = len(queue) - 9
    ending = '' if remains < 0 else f'\nи еще ({remains}) ...'
    return f'{result}{ending}'


class Music(MusicBase):
    def __init__(self, bot) -> None:
        super(Music, self).__init__(bot)
        self.view = PlayerButtonsView(self._pause, self._skip,
                                      self._queue, self._favorite)

    async def _get_context(self, interaction: discord.Interaction, command_name: str):
        try:
            ctx: commands.Context = await self.bot.get_context(interaction)
        except ValueError:
            guild = self.bot.get_guild(interaction.guild_id)
            command = type('Command', tuple(), {'name': command_name})
            ctx = type('Context', tuple(), {'guild': guild, 'author': guild.get_member(interaction.user.id),
                                            'command': command, 'voice_client': None, 'channel': interaction.channel,
                                            'me': interaction.client.user})
        return ctx

    @app_commands.command(description='Ссылка или часть названия трека')
    async def play(self, interaction: discord.Interaction, query: str) -> None:
        await self._play(interaction, query)

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

        user_id = interaction.user.id
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

        try:
            msg = await interaction.response.send_message(embed=embed, ephemeral=False, delete_after=30)
            await self.db.create_sent_message(msg.id)
        finally:
            if not player.is_playing:
                await player.play()

    @app_commands.command(description='Очищает очередь и останавливает исполнение')
    async def stop(self, interaction: discord.Interaction) -> None | discord.Message:
        """ Disconnects the player from the voice channel and clears its queue. """
        ctx: commands.Context = await self.bot.get_context(interaction)
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not ctx.voice_client:
            raise not_connected

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            raise not_same_voicechat

        player.queue.clear()

        try:
            await self.clear_player_message(player)
        finally:
            await player.stop()
            await ctx.voice_client.disconnect(force=True)
            msg = 'Принудительно завершено исполнение!'
            await self.log_message(interaction.response.send_message(msg, ephemeral=False, delete_after=30))

    @app_commands.command(description='Очередь исполнения')
    async def queue(self, interaction: discord.Interaction) -> None:
        await self._queue(interaction)

    async def _queue(self, interaction: discord.Interaction) -> None:
        ctx = await self._get_context(interaction, command_name='queue')

        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if player is None or (not player.is_playing and not player.queue):
            raise discord.app_commands.AppCommandError('Очередь пуста!')

        queue_msg = queue_repr(player.queue, player.current.title)
        await self.log_message(interaction.response.send_message(queue_msg, ephemeral=False, delete_after=30))

    @app_commands.command(description='Быстрый заказ избранных треков')
    async def favorite(self, interaction: discord.Interaction) -> None:
        await self._favorite(interaction)

    async def _favorite(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message('Список избранных треков отправлен в ЛС',
                                                ephemeral=True, delete_after=10)
        user = interaction.user
        favorites = await self.db.get_user_favorite_music(user.id)
        try:
            view = create_view('Выберите трек для добавления в очередь', favorites,
                               interaction.guild_id, handler=self._play)
            await self.log_message(user.send(view=view, delete_after=60))
        except AttributeError:
            await self.log_message(user.send('У вас нет избранных треков. Возможно, вы не ставили никаких треков.'))

    @app_commands.command(description='Пауза текущего трека')
    async def pause(self, interaction: discord.Interaction) -> None:
        await self._pause(interaction)

    async def _pause(self, interaction: discord.Interaction) -> None:
        player: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(interaction.guild_id)
        player.paused = not player.paused
        status = "приостановлено" if player.paused else "вознобновлено"
        try:
            msg = f'Воспроизведение {status}! \nПользователь: {interaction.user.mention}'
            await self.log_message(interaction.response.send_message(msg, ephemeral=False, delete_after=15))
        except AttributeError:
            pass
        await player.set_pause(player.paused)
        await self.update_msg(player)

    @app_commands.command(description='Пропуск текущего трека')
    async def skip(self, interaction: discord.Interaction) -> None:
        await self._skip(interaction)

    async def _skip(self, interaction: discord.Interaction) -> None:
        player = self.bot.lavalink.player_manager.get(interaction.guild_id)
        try:
            msg = f'Пропущено воспроизведение трека {player.current.title}! \nПользователь: {interaction.user.mention}'
            await self.log_message(interaction.response.send_message(msg, ephemeral=False, delete_after=15))
        except AttributeError:
            pass
        await player.skip()
        await self.update_msg(player)


async def setup(bot):
    guild_id = envs['guild_id']
    await bot.add_cog(Music(bot), guilds=[discord.Object(id=guild_id)])
