import asyncio
import datetime
from contextlib import suppress

import discord
from cachetools import TTLCache
from discord.ext import commands
from sqlalchemy.exc import IntegrityError

from .views import LoggerView
from config import Config
from utils import now
from bot.mixins import DiscordFeaturesMixin


def create_embed(
    name: str,
    members: str,
    creator: discord.Member,
    begin: str,
    end: str = None,
    duration: str = None,
    thumbnail_url: str = None,
    footer_text: str = None,
    footer_url: str = None,
) -> discord.Embed:
    embed = discord.Embed()
    embed.add_field(name=f'├ Время начала', value=f'├ **`{begin}`**')

    if not end:  # session create
        embed.title = f"Активен сеанс: {name}"
        embed.colour = discord.Color.green()
        embed.add_field(name='Текущий лидер', value=creator.mention)
        embed.set_footer(text=creator.display_name + " - Создатель сессии",
                         icon_url=creator.display_avatar)
    else:  # session over
        embed.title = f"Сеанс {name} окончен!"
        embed.colour = discord.Color.red()
        embed.add_field(name='Время окончания', value=f'**`{end}`**')
        embed.add_field(name='├ Продолжительность', value=duration,
                        inline=False)
        embed.set_thumbnail(url=thumbnail_url)
        embed.set_footer(text=footer_text, icon_url=footer_url)

    embed.add_field(name='├ Участники', value=members, inline=False)

    return embed


class LoggerHelpers:
    bot = db = None

    @staticmethod
    def get_voice_channel(user: discord.Member):
        return user.voice.channel if user.voice else None

    @staticmethod
    def fmt(dt: datetime.datetime) -> str:
        return dt.strftime('%H:%M %d.%m.%y')

    @staticmethod
    def dt_from_str(s: str) -> datetime.datetime:
        return datetime.datetime.strptime(s[:19], '%Y-%m-%d %H:%M:%S')

    def datetime_handler(self, x):
        return self.fmt(self.dt_from_str(x)) if x else '-'

    async def restore_log_session_message(
        self,
        from_date: datetime.datetime | None = None,
        to_date: datetime.datetime | None = None
    ):
        guild = self.bot.guilds[0]
        for session in await self.db.get_all_sessions(from_date, to_date):

            name = session['name']
            begin = self.dt_from_str(session['begin'])
            end = self.dt_from_str(session['end'])

            creator = guild.get_member(session['creator_id'])
            sess_duration = end - begin

            duration_field = f"├ **`{str(sess_duration).split('.')[0]}`**"
            members_field = '└ ' + ', '.join(
                f'<@{member["id"]}>' for member in
                await self.db.get_session_members(session['channel_id'])
            )

            if sess_duration.seconds < Logger.MIN_SESS_DURATION:
                return

            embed = create_embed(
                name,
                self.fmt(begin),
                self.fmt(end),
                duration_field,
                members_field,
                creator,
            )

            msg = await self.bot.channel.logger.send(
                embed=embed,
                view=LoggerView(self.bot, self.datetime_handler)
            )
            await self.db.session_update(channel_id=session['channel_id'],
                                         message_id=msg.id)

    async def wait_for_session_created(self, session_id: int):
        def check(channel_id: int, _):
            return channel_id == session_id

        result = await self.bot.wait_for('db_session_created', check=check)
        return result


class LoggerEventHandlers(DiscordFeaturesMixin, LoggerHelpers):
    def __init__(self, bot):
        super(LoggerEventHandlers, self).__init__(bot)

        # cache stores items only 2 seconds
        self.cache = TTLCache(maxsize=100, ttl=2)

        self.bot.loop.create_task(self.register_logger_views())
        self.bot.loop.create_task(self.add_members())

    async def register_logger_views(self):
        sessions = await self.db.get_all_sessions()
        for session in sessions:
            view = LoggerView(self.bot, self.datetime_handler)
            self.bot.add_view(view, message_id=session['message_id'])

    async def add_members(self):
        tasks = (self.db.user_create(id=member.id, name=member.display_name)
                 for member in self.bot.guilds[0].members)
        with suppress(IntegrityError):
            await asyncio.gather(*tasks)

    async def update_embed_members(self, session_id: int):

        session = await self.db.get_session(session_id)
        msg_id = session['message_id']

        message = await self.bot.channel.logger.fetch_message(msg_id)
        members = await self.db.get_session_members(session_id)
        embed = message.embeds[0]

        embed.set_field_at(
            2,
            name='├ Участники',
            value='└ ' + ', '.join(f'<@{member["id"]}>' for member in members),
            inline=False
        )
        await message.edit(embed=embed)

    async def update_activity_icon(self, channel_id: int, app_id: int):
        session = await self.db.get_session(channel_id)
        app_info = await self.db.get_activity_info(app_id)
        if session and app_info:
            message_id, thumbnail_url = session['message_id'], app_info[
                'icon_url']
            msg = await self.bot.channel.logger.fetch_message(message_id)
            embed = msg.embeds[0]
            embed.set_thumbnail(url=thumbnail_url)
            await msg.edit(embed=embed)
            if emoji := await self.db.get_activity_emoji(app_id):
                await msg.add_reaction(self.bot.get_emoji(emoji['id']))

    async def _member_join_channel(self, member_id: int, session_id: int):
        async def _add_member():
            try:
                await self.db.session_add_member(session_id, member_id)
            except ValueError:  # session still not created
                await self.wait_for_session_created(session_id)
                await _add_member()

            await self.update_embed_members(session_id)

        await _add_member()
        await self.db.prescence_update(
            channel_id=session_id,
            member_id=member_id,
            begin=now()
        )

    async def _member_abandon_channel(self, member_id: int, channel_id: int):
        await self.db.prescence_update(
            member_id=member_id,
            channel_id=channel_id,
            end=now()
        )


class Logger(LoggerEventHandlers):
    MIN_SESS_DURATION = Config.MIN_SESS_DURATION  # in seconds

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self.db.user_create(id=member.id, name=member.display_name)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ):
        if before.channel == after.channel:  # mute or deaf
            return

        # User join to foreign channel (leave considered the same)
        if after.channel and after.channel != self.bot.channel.create:
            await self._member_join_channel(member.id, after.channel.id)

        if before.channel and before.channel != self.bot.channel.create:
            await self._member_abandon_channel(member.id, before.channel.id)

    @commands.Cog.listener()
    async def on_member_join_channel(self, member_id: int, channel_id: int):
        await self._member_join_channel(member_id, channel_id)

    @commands.Cog.listener()
    async def on_db_session_created(self, channel_id: int, message_id: int):
        pass

    @commands.Cog.listener()
    async def on_session_begin(
        self, creator: discord.Member,
        channel: discord.VoiceChannel
    ):
        begin = now()
        name = channel.name

        embed = create_embed(
            name,
            '└ ' + f'<@{creator.id}>',
            creator,
            self.fmt(begin)
        )

        msg = await self.bot.channel.logger.send(
            embed=embed,
            view=LoggerView(self.bot, self.datetime_handler)
        )
        await self.db.session_update(
            name=name,
            creator_id=creator.id,
            leader_id=creator.id,
            channel_id=channel.id,
            begin=begin,
            message_id=msg.id
        )
        self.bot.dispatch("db_session_created", channel.id, msg.id)
        self.bot.dispatch("activity", None, creator)

    @commands.Cog.listener()
    async def on_session_over(self, channel_id: int):
        session = await self.db.get_session(channel_id)
        if session is None:
            return

        name, msg_id = session['name'], session['message_id']
        try:
            msg = await self.bot.channel.logger.fetch_message(msg_id)
        except discord.NotFound:
            return

        begin = self.dt_from_str(session['begin'])
        end = now()
        sess_duration = end - begin

        await self.db.update_leader(channel_id=channel_id, member_id=None,
                                    begin=end)
        await self.db.session_update(channel_id=channel_id, end=end)

        if sess_duration.seconds < Logger.MIN_SESS_DURATION:
            with suppress(discord.NotFound):
                await msg.delete()
            return

        duration_field = f"├ **`{str(sess_duration).split('.')[0]}`**"
        members_mention = (f'<@{member["id"]}>' for member in
                           await self.db.get_session_members(channel_id))
        members_field = '└ ' + ', '.join(members_mention)

        embed = create_embed(
            name,
            members_field,
            None,
            self.fmt(begin),
            self.fmt(end),
            duration_field,
            msg.embeds[0].thumbnail.url,
            msg.embeds[0].footer.text,
            msg.embeds[0].footer.icon_url
        )

        await msg.edit(embed=embed)

    @commands.Cog.listener()
    async def on_activity(
        self,
        before: discord.Member | None,
        after: discord.Member
    ):
        dt = now()

        voice_channel = self.get_voice_channel(after)
        before_app_id = self.get_app_id(before)
        after_app_id = self.get_app_id(after)

        if after_app_id and not self.cache.get(after):
            # for source reason discord rest calling event on_prescence_update
            # twice with same data
            self.cache[after] = dt.isoformat()
            await self.db.member_activity(
                member_id=after.id,
                id=after_app_id,
                begin=dt,
                end=None,
            )
            if voice_channel is not None:  # logging activities of user in channel
                await self.update_activity_icon(voice_channel.id, after_app_id)

        if before_app_id and not self.cache.get(before):
            self.cache[before] = dt.isoformat()
            await self.db.member_activity(
                member_id=before.id,
                id=before_app_id,
                end=dt
            )

    @commands.Cog.listener()
    async def on_leader_change(self, channel_id: int, leader: discord.Member):
        session = await self.db.get_session(channel_id)
        if not session:
            return

        msg = await self.bot.channel.logger.fetch_message(session['message_id'])
        name = await self.get_user_sess_name(leader)
        embed: discord.Embed = msg.embeds[0]
        embed.title = f"Активен сеанс: {name}"
        embed.set_field_at(1, name='Текущий лидер', value=f'<@{leader.id}>')
        await msg.edit(embed=embed)
        await self.db.update_leader(
            channel_id=channel_id,
            member_id=leader.id,
            begin=now()
        )