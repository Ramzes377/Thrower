import re

import discord
from discord import app_commands
from discord.ext import commands
# from discord_ui.cogs import slash_command, subslash_command

from api.cogs.music_core.views import create_dropdown, PlayerButtonsView
from api.cogs.music_core.music_cog_core import MusicCore
from api.cogs.music_core.query_cache import write_music_query, mru_queries

url_rx = re.compile(r'https?://(?:www\.)?.+')


def queue_repr(queue: list, current: str) -> str:
    wrap = '```'
    others = '\n'.join(map(lambda x: f"{x[0]}. {x[1].title}", enumerate(queue, start=2)))
    return f'{wrap}1. {current}\n{others}{wrap}'[:1975] + '\n...'


class Music(MusicCore):
    def __init__(self, bot):
        super(Music, self).__init__(bot)
        self._text_channel = None
        self._msg = None
        self._guild_id = None
        self._paused = False

    @commands.command()
    async def sync(self, ctx):
        print(await ctx.bot.tree.sync(guild=ctx.guild))

    @app_commands.command(description='Ссылка или часть названия трека.')
    async def play(self, interaction: discord.Interaction, query: str) -> None:
        await self._play(interaction, query)

    async def _play(self, interaction: discord.Interaction, query: str) -> None:
        """ Searches and plays a song from a given query. """
        try:
            ctx: commands.Context = await self.bot.get_context(interaction)
            self._guild_id = interaction.guild_id
            self._text_channel = interaction.channel
        except ValueError:
            guild = self.bot.guilds[0]
            command = type('Command', tuple(), {'name': 'play'})
            ctx = type('Context', tuple(), {'guild': guild, 'author': guild.get_member(interaction.user.id),
                                            'command': command, 'voice_client': None, 'channel': interaction.channel,
                                            'me': interaction.client.user})
            self._guild_id = self.bot.guilds[0].id
            self._text_channel = self.bot.get_channel(866284793313624064)

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

        await self._text_channel.send(embed=embed, delete_after=30)

        if not player.is_playing:
            await player.play()

    @commands.command(name='stop', aliases=['dc'])
    async def _stop(self, ctx):
        """ Disconnects the player from the voice channel and clears its queue. """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not ctx.voice_client:
            return await ctx.send('Not connected.', delete_after=30)

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            return await ctx.send('You\'re not in my voicechannel!', delete_after=30)

        player.queue.clear()

        await player.stop()
        await ctx.voice_client.disconnect(force=True)
        await ctx.send('*⃣ | Disconnected.', delete_after=30)

    @commands.command(name='queue')
    async def _queue(self, ctx: discord.ext.commands.Context) -> None:
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not player.is_playing and not player.queue:
            await ctx.send('Очередь пуста!', delete_after=20)
            return
        queue_msg = queue_repr(player.queue, player.current.title)
        await ctx.send(queue_msg, delete_after=30)

    @commands.command(name='preferences', aliases=['history', 'favorite'])
    async def _preferences(self, ctx):
        user = ctx.message.author
        prefences = mru_queries(user.id)
        #ctx.command.name = 'play'  # change command name from preferences to ensure voice channel
        try:
            await user.send(
                view=create_dropdown('Выберите трек для добавления в очередь', prefences, ctx.channel, handler=self._play),
                delete_after=60)
        except AttributeError:
            await user.send('У вас нет избранных треков. Возможно, вы не ставили никаких треков.')

    async def _pause(self):
        player = self.bot.lavalink.player_manager.get(self._guild_id)
        self._paused = not self._paused
        await player.set_pause(self._paused)
        await self.update_msg()

    async def _skip(self):
        player = self.bot.lavalink.player_manager.get(self._guild_id)
        await player.skip()
        await self.update_msg()

    async def update_msg(self) -> None:
        player = self.bot.lavalink.player_manager.get(self._guild_id)
        if not player.current:
            return

        status = ':musical_note: Играет :musical_note:' if not self._paused else ':pause_button: Пауза :pause_button:'
        if self._msg:
            embed = self._msg.embeds[0]
            embed.set_field_at(0, name='Текущий трек', value=player.current.title)
            embed.set_field_at(1, name='Статус', value=status, inline=False)
            await self._msg.edit(embed=embed)
            return

        embed = (discord.Embed(color=discord.Color.blurple())
                 .add_field(name='Текущий трек', value=player.current.title)
                 .add_field(name='Статус', value=status, inline=False)
                 .set_footer(text='Великий бот - ' + self.bot.user.display_name, icon_url=self.bot.user.avatar))
        msg = await self._text_channel.send(embed=embed, view=PlayerButtonsView(self._pause, self._skip))
        self._msg = msg


async def setup(bot):
    await bot.add_cog(Music(bot), guilds=[discord.Object(id=257878464667844618)])
