import re

import discord
import lavalink
from discord import app_commands
from discord.ext import commands

from api.cogs.music_core.views import create_dropdown, PlayerButtonsView
from api.cogs.music_core.music_cog_core import MusicCore
from api.cogs.music_core.query_cache import write_music_query, mru_queries

url_rx = re.compile(r'https?://(?:www\.)?.+')


def queue_repr(queue: list, current: str) -> str:
    wrap = '```'
    others = '\n'.join(map(lambda x: f"{x[0]}. {x[1].title}", enumerate(queue[:9], start=2)))
    result = f'{wrap}1. {current}\n{others}'
    remains = len(queue) - 9
    ending = '' if remains < 0 else f'\nи еще ({remains}) трека ...'
    return f'{result}{ending}{wrap}'


class Music(MusicCore):
    def __init__(self, bot) -> None:
        super(Music, self).__init__(bot)
        self._text_channel = None
        self._msg = None
        self._guild_id = None
        self._paused = False
        lavalink.add_event_hook(self.events_handler)

    async def events_handler(self, event: lavalink.events.Event):
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

    @commands.command()
    async def sync(self, ctx: commands.Context) -> None:
        print(await ctx.bot.tree.sync(guild=ctx.guild))

    def _custom_context(self, interaction: discord.Interaction, command_name: str) -> type:
        guild = self.bot.guilds[0]
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
        try:
            ctx: commands.Context = await self.bot.get_context(interaction)
            self._guild_id = interaction.guild_id
            self._text_channel = interaction.channel
        except ValueError:
            ctx = self._custom_context(interaction, command_name='play')
            self._guild_id = self.bot.guilds[0].id
            self._text_channel = self.bot.commands_channel

        await self.ensure_voice(ctx)
        player = self.bot.lavalink.player_manager.get(self._guild_id)
        query = query.strip('<>')
        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        results = await player.node.get_tracks(query)

        if not results or not results.tracks:
            return await self._text_channel.send('Nothing found!', delete_after=30)

        user_id = interaction.user.id
        embed = discord.Embed(color=discord.Color.blurple())
        if results.load_type == 'PLAYLIST_LOADED':
            tracks = results.tracks
            for track in tracks:
                player.add(requester=user_id, track=track)
            embed.title = 'Плейлист добавлен в очередь!'
            embed.description = f'{results.playlist_info.name} - {len(tracks)} tracks'
            write_music_query(results.playlist_info.name, user_id, query)
        else:
            track = results.tracks[0]
            embed.title = 'Трек добавлен в очередь!'
            embed.description = f'[{track.title}]({track.uri})'
            player.add(requester=user_id, track=track)
            write_music_query(track.title, user_id, track.uri)

        try:
            await interaction.response.send_message(embed=embed, ephemeral=False, delete_after=30)
        except discord.errors.InteractionResponded:
            pass

        if not player.is_playing:
            await player.play()

    @app_commands.command(description='Очищает очередь и останавливает исполнение')
    async def stop(self, interaction: discord.Interaction) -> None:
        """ Disconnects the player from the voice channel and clears its queue. """
        ctx: commands.Context = await self.bot.get_context(interaction)
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not ctx.voice_client:
            return await ctx.send('Not connected.', delete_after=30)

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            return await ctx.send('You\'re not in my voicechannel!', delete_after=30)

        player.queue.clear()

        await player.stop()
        await ctx.voice_client.disconnect(force=True)
        await ctx.send('*⃣ | Disconnected.', delete_after=30)

    @app_commands.command(description='Очередь исполнения')
    async def queue(self, interaction: discord.Interaction) -> None:
        await self._queue(interaction)

    async def _queue(self, interaction: discord.Interaction) -> None:
        try:
            ctx: commands.Context = await self.bot.get_context(interaction)
        except ValueError:
            ctx = self._custom_context(interaction, command_name='queue')

        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if player is None or (not player.is_playing and not player.queue):
            await interaction.response.send_message('Очередь пуста!', delete_after=30)
            return
        queue_msg = queue_repr(player.queue, player.current.title)
        await interaction.response.send_message(queue_msg, ephemeral=False, delete_after=30)

    @app_commands.command(description='Быстрый заказ избранных треков')
    async def favorite(self, interaction: discord.Interaction) -> None:
        await self._favorite(interaction)

    async def _favorite(self, interaction: discord.Interaction) -> None:
        try:
            await interaction.response.send_message('Список избранных треков отправлен в ЛС',
                                                    ephemeral=True, delete_after=10)
            ctx: commands.Context = await self.bot.get_context(interaction)
            user = ctx.message.author
        except ValueError:
            ctx = self._custom_context(interaction, command_name='favorite')
            user = ctx.author

        favorite = mru_queries(user.id)
        try:
            await user.send(
                view=create_dropdown('Выберите трек для добавления в очередь', favorite, handler=self._play),
                delete_after=60)
        except AttributeError:
            await user.send('У вас нет избранных треков. Возможно, вы не ставили никаких треков.')

    @app_commands.command(description='Пауза текущего трека')
    async def pause(self, interaction: discord.Interaction) -> None:
        await self._pause(interaction)

    async def _pause(self, interaction: discord.Interaction) -> None:
        player = self.bot.lavalink.player_manager.get(self._guild_id)
        self._paused = not self._paused
        await interaction.response.send_message(
            f'Воспроизведение {"приостановлено" if self._paused else "вознобновлено"}!',
            ephemeral=False, delete_after=15)
        await player.set_pause(self._paused)
        await self.update_msg()

    @app_commands.command(description='Пропуск текущего трека')
    async def skip(self, interaction: discord.Interaction) -> None:
        await self._skip(interaction)

    async def _skip(self, interaction: discord.Interaction) -> None:
        player = self.bot.lavalink.player_manager.get(self._guild_id)
        await interaction.response.send_message(f'Пропущено воспроизведение трека {player.current.title}',
                                                ephemeral=False, delete_after=15)
        await player.skip()
        await self.update_msg()

    async def update_msg(self) -> None:
        """Creates a player UI bar"""
        player = self.bot.lavalink.player_manager.get(self._guild_id)
        if not player.current:
            return

        current_track = player.current.title
        status = ':musical_note: Играет :musical_note:' if not self._paused else ':pause_button: Пауза :pause_button:'
        if self._msg:
            # when we calling it and message already exists then we expect to change ONLY current track or playing status
            embed = self._msg.embeds[0]
            embed.set_field_at(0, name='Текущий трек', value=current_track)
            embed.set_field_at(1, name='Статус', value=status, inline=False)
            try:
                await self._msg.edit(embed=embed)
            except discord.errors.NotFound:  # message were deleted for some reason, just recreate it
                self._msg = None
                await self.update_msg()
            return

        embed = (discord.Embed(color=discord.Color.blurple())
                 .add_field(name='Текущий трек', value=current_track)
                 .add_field(name='Статус', value=status, inline=False)
                 .set_footer(text='Великий бот - ' + self.bot.user.display_name, icon_url=self.bot.user.avatar))
        self._msg = await self._text_channel.send(embed=embed,
                                                  view=PlayerButtonsView(self._pause, self._skip,
                                                                         self._queue, self._favorite))


async def setup(bot):
    await bot.add_cog(Music(bot), guilds=[discord.Object(id=257878464667844618)])
