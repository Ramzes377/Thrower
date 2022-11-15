import re
from functools import partial

import discord
from discord.ext import commands
import interactions
# from discord.ui import view
# from discord_ui import SlashOption
# from discord_ui.cogs import slash_command, subslash_command, context_cog, listening_component
from api.cogs.music_core.views import create_dropdown, PlayerButtonsView
from api.cogs.music_core.music_cog_core import MusicCore
from api.cogs.music_core.query_cache import write_music_query, mru_queries

url_rx = re.compile(r'https?://(?:www\.)?.+')


def queue_repr(queue: list, current: str) -> str:
    wrap = '```'
    others = '\n'.join(map(lambda x: f"{x[0]}. {x[1].title}", enumerate(queue, start=2)))
    return f'{wrap}1. {current}\n{others}{wrap}'


class Music(MusicCore):
    def __init__(self, bot):
        super(Music, self).__init__(bot)
        self._text_channel = None
        self._msg = None
        self._guild_id = None
        self._paused = False

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        user_bot = payload.member.bot
        music_msg = await self._text_channel.fetch_message(payload.message_id) == self._msg
        if not user_bot and music_msg:
            player = self.bot.lavalink.player_manager.get(self._guild_id)
            if payload.emoji.name in ('➡️', '⏯️'):
                if payload.emoji.name == '➡️':
                    await player.skip()
                else:
                    self._paused = not self._paused
                    await player.set_pause(self._paused)
                await self.update_msg()

    @commands.command(name='play', aliases=['p'])
    # @slash_command(options=[SlashOption(str, name='play', description="this is a parameter",
    #                                     choices=[{"name": "choice 1", "value": "test"}])],
    #                guild_ids=[257878464667844618],
    #                default_permission=False)
    async def _play(self, ctx, *, query: str):
        """ Searches and plays a song from a given query. """
        self._guild_id = ctx.guild.id
        self._text_channel = ctx.channel

        player = self.bot.lavalink.player_manager.get(self._guild_id)
        query = query.strip('<>')
        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        results = await player.node.get_tracks(query)

        if not results or not results.tracks:
            return await ctx.send('Nothing found!', delete_after=30)

        embed = discord.Embed(color=discord.Color.blurple())
        if results.load_type == 'PLAYLIST_LOADED':
            tracks = results.tracks
            for track in tracks:
                player.add(requester=ctx.author.id, track=track)
            embed.title = 'Плейлист добавлен в очередь!'
            embed.description = f'{results.playlist_info.name} - {len(tracks)} tracks'
            write_music_query(results.playlist_info.name, ctx.message.author.id, query)
        else:
            track = results.tracks[0]
            embed.title = 'Трек добавлен в очередь!'
            embed.description = f'[{track.title}]({track.uri})'
            player.add(requester=ctx.author.id, track=track)
            write_music_query(track.title, ctx.message.author.id, track.uri)

        await ctx.send(embed=embed, delete_after=30)

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

    async def update_msg(self) -> None:
        player = self.bot.lavalink.player_manager.get(self._guild_id)
        if player.current:
            status = ':musical_note: Играет :musical_note:' if not self._paused else ':pause_button: Пауза :pause_button:'
            if not self._msg:
                embed = (discord.Embed(color=discord.Color.blurple())
                         .add_field(name='Текущий трек', value=player.current.title)
                         .add_field(name='Статус', value=status, inline=False)
                         .set_footer(text='Великий бот - ' + self.bot.user.display_name, icon_url=self.bot.user.avatar))
                msg = await self._text_channel.send(embed=embed, view=PlayerButtonsView(player.set_pause, player.skip))
                self._msg = msg
            else:
                embed = self._msg.embeds[0]
                embed.set_field_at(0, name='Текущий трек', value=player.current.title)
                embed.set_field_at(1, name='Статус', value=status, inline=False)
                await self._msg.edit(embed=embed)

    @commands.command(name='preferences', aliases=['history', 'favorite'])
    async def _preferences(self, ctx):
        user = ctx.message.author
        prefences = mru_queries(user.id)
        ctx.command.name = 'play'  # change command name from preferences to ensure voice channel
        try:
            await user.send(view=create_dropdown('Выберите трек для добавления в очередь', prefences,
                                                 handlers=[partial(self.ensure_voice, ctx), partial(self._play, ctx)]),
                            delete_after=60)
        except AttributeError:
            await user.send(
                'У вас нет избранных треков. Использование команды !play *query* автоматически добавит их туда.'
            )


async def setup(bot):
    await bot.add_cog(Music(bot))
