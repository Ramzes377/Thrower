import asyncio
import datetime
from contextlib import suppress

import discord
from cachetools import TTLCache
from discord.ext import commands
from sqlalchemy.exc import IntegrityError

from settings import tzMoscow
from .views import LoggerView
from ...mixins import DiscordFeaturesMixin


def now() -> datetime:
    return datetime.datetime.now(tz=tzMoscow).replace(microsecond=0, tzinfo=None)


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

    async def restore_log_session_message(self, from_date: datetime.datetime | None = None,
                                          to_date: datetime.datetime | None = None):
        guild = self.bot.guilds[0]
        for session in await self.db.get_all_sessions(from_date, to_date):

            name = session['name']
            begin = self.dt_from_str(session['begin'])
            end = self.dt_from_str(session['end'])

            creator = guild.get_member(session['creator_id'])
            sess_duration = end - begin

            duration_field = f"├ **`{str(sess_duration).split('.')[0]}`**"
            members_field = '└ ' + ', '.join(
                f'<@{member["id"]}>' for member in await self.db.get_session_members(session['channel_id'])
            )

            if sess_duration.seconds < Logger.MIN_SESS_DURATION:
                return

            embed = (
                discord.Embed(title=f"Сеанс {name} окончен!", color=discord.Color.red())
                .add_field(name=f'├ Время начала', value=f'├ **`{self.fmt(begin)}`**')
                .add_field(name='Время окончания', value=f'**`{self.fmt(end)}`**')
                .add_field(name='├ Продолжительность', value=duration_field, inline=False)
                .add_field(name='├ Участники', value=members_field, inline=False)
                .set_footer(text=creator.display_name + " - Создатель сессии", icon_url=creator.display_avatar)
            )

            msg = await self.bot.logger_channel.send(embed=embed, view=LoggerView(self.bot, self.datetime_handler))
            await self.db.session_update(channel_id=session['channel_id'], message_id=msg.id)

    async def wait_for_session_created(self, session_id: int):
        def check(channel_id: int, _):
            return channel_id == session_id

        result = await self.bot.wait_for('db_session_created', check=check)
        return result


class LoggerEventHandlers(DiscordFeaturesMixin, LoggerHelpers):
    def __init__(self, bot):
        super(LoggerEventHandlers, self).__init__(bot)
        self.cache = TTLCache(maxsize=100, ttl=2)  # cache stores items only 2 seconds
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
        try:
            msg_id = session['message_id']
        except TypeError:
            _, msg_id = await self.wait_for_session_created(session_id)

        message = await self.bot.logger_channel.fetch_message(msg_id)
        members = await self.db.get_session_members(session_id)
        embed = message.embeds[0]

        embed.set_field_at(2, name='├ Участники',
                           value='└ ' + ', '.join(f'<@{member["id"]}>' for member in members),
                           inline=False)
        await message.edit(embed=embed)

    async def update_activity_icon(self, channel_id: int, app_id: int):
        session = await self.db.get_session(channel_id)
        app_info = await self.db.get_activity_info(app_id)
        if session and app_info:
            message_id, thumbnail_url = session['message_id'], app_info['icon_url']
            msg = await self.bot.logger_channel.fetch_message(message_id)
            embed = msg.embeds[0]
            embed.set_thumbnail(url=thumbnail_url)
            await msg.edit(embed=embed)
            if emoji := await self.db.get_activity_emoji(app_id):
                await msg.add_reaction(self.bot.get_emoji(emoji['id']))

    async def _member_join_channel(self, member_id: int, session_id: int):
        try:
            add = await self.db.session_add_member(session_id, member_id)
        except IntegrityError:
            add = True

        if not add:  # session still not created
            await self.wait_for_session_created(session_id)
            await self.db.session_add_member(session_id, member_id)
            await self.update_embed_members(session_id)

        await self.db.prescence_update(channel_id=session_id, member_id=member_id, begin=now())

    async def _member_abandon_channel(self, member_id: int, channel_id: int):
        await self.db.prescence_update(member_id=member_id, channel_id=channel_id, end=now())


class Logger(LoggerEventHandlers):
    MIN_SESS_DURATION = 5 * 60  # in seconds

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self.db.user_create(id=member.id, name=member.display_name)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
        # User join to foreign channel (leave considered the same)
        if after.channel and after.channel != self.bot.create_channel:
            await self._member_join_channel(member.id, after.channel.id)

        if before.channel and before.channel != self.bot.create_channel:
            await self._member_abandon_channel(member.id, before.channel.id)

    @commands.Cog.listener()
    async def on_member_join_channel(self, member_id: int, channel_id: int):
        await self._member_join_channel(member_id, channel_id)

    @commands.Cog.listener()
    async def on_db_session_created(self, channel_id: int, message_id: int):
        pass

    @commands.Cog.listener()
    async def on_session_begin(self, creator_id: discord.Member, channel: discord.VoiceChannel):
        begin = now()
        creator = channel.guild.get_member(creator_id)
        name = channel.name

        embed = (
            discord.Embed(title=f"Активен сеанс: {name}", color=discord.Color.green())
            .add_field(name=f'├ Время начала', value=f'├ **`{self.fmt(begin)}`**')
            .add_field(name='Текущий лидер', value=creator.mention)
            .add_field(name='├ Участники', value='└ ' + f'<@{creator.id}>', inline=False)
            .set_footer(text=creator.display_name + " - Создатель сессии", icon_url=creator.display_avatar)
        )

        msg = await self.bot.logger_channel.send(embed=embed, view=LoggerView(self.bot, self.datetime_handler))
        await self.db.session_update(
            name=name,
            creator_id=creator_id,
            leader_id=creator_id,
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

        sess_name, msg_id = session['name'], session['message_id']
        try:
            msg = await self.bot.logger_channel.fetch_message(msg_id)
        except discord.NotFound:
            return

        begin = self.dt_from_str(session['begin'])
        end = now()
        sess_duration = end - begin

        await self.db.update_leader(channel_id=channel_id, member_id=None, begin=end)
        await self.db.session_update(channel_id=channel_id, end=end)

        if sess_duration.seconds < Logger.MIN_SESS_DURATION:
            try:
                await msg.delete()
            finally:
                return

        duration_field = f"├ **`{str(sess_duration).split('.')[0]}`**"
        members_mention = (f'<@{member["id"]}>' for member in await self.db.get_session_members(channel_id))
        members_field = '└ ' + ', '.join(members_mention)
        embed = (
            discord.Embed(title=f"Сеанс {sess_name} окончен!", color=discord.Color.red())
            .add_field(name=f'├ Время начала', value=f'├ **`{self.fmt(begin)}`**')
            .add_field(name='Время окончания', value=f'**`{self.fmt(end)}`**')
            .add_field(name='├ Продолжительность', value=duration_field, inline=False)
            .add_field(name='├ Участники', value=members_field, inline=False)
            .set_footer(text=msg.embeds[0].footer.text, icon_url=msg.embeds[0].footer.icon_url)
            .set_thumbnail(url=msg.embeds[0].thumbnail.url)
        )
        await msg.edit(embed=embed)

    @commands.Cog.listener()
    async def on_activity(self, before: discord.Member | None, after: discord.Member):
        dt = now()

        voice_channel = self.get_voice_channel(after)
        before_app_id = self.get_app_id(before)
        after_app_id = self.get_app_id(after)

        if after_app_id and not self.cache.get(after):
            # for some reason discord rest calling event on_prescence_update twice with same data
            self.cache[after] = dt.isoformat()
            await self.db.member_activity(member_id=after.id, id=after_app_id, begin=dt, end=None)
            if voice_channel is not None:  # logging activities of user in channel
                await self.update_activity_icon(voice_channel.id, after_app_id)

        if before_app_id and not self.cache.get(before):
            self.cache[before] = dt.isoformat()
            await self.db.member_activity(member_id=before.id, id=before_app_id, end=dt)

    @commands.Cog.listener()
    async def on_leader_change(self, channel_id: int, leader: discord.Member):
        session = await self.db.get_session(channel_id)
        if not session:
            return

        msg = await self.bot.logger_channel.fetch_message(session['message_id'])
        name = await self.get_user_sess_name(leader)
        embed: discord.Embed = msg.embeds[0]
        embed.title = f"Активен сеанс: {name}"
        embed.set_field_at(1, name='Текущий лидер', value=f'<@{leader.id}>')
        await msg.edit(embed=embed)
        await self.db.update_leader(channel_id=channel_id, member_id=leader.id, begin=now())
