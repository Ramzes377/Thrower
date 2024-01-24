import asyncio
from collections import defaultdict
from datetime import datetime
from contextlib import suppress
from typing import TYPE_CHECKING, Optional

from cachetools import TTLCache
from discord import Embed, Color, NotFound
from discord.ext.commands import Cog

from src.constants import constants
from src.config import Config
from src.utils import now, create_if_not_exists
from src.bot.mixins import DiscordFeaturesMixin
from .views import LoggerView

if TYPE_CHECKING:
    from discord import Member, VoiceChannel, VoiceState, Guild, Emoji


def create_embed(
        name: str,
        members: str,
        creator: Optional['Member'],
        begin: str,
        end: str = None,
        duration: str = None,
        thumbnail_url: str = None,
        footer_text: str = None,
        footer_url: str = None,
) -> Embed:
    embed = Embed()
    embed.add_field(name=f'├ Время начала', value=f'├ **`{begin}`**')

    if not end:  # session create
        embed.title = f"Активен сеанс: {name}"
        embed.colour = Color.green()
        embed.add_field(name='Текущий лидер', value=creator.mention)
        embed.set_footer(text=creator.display_name + " - Создатель сессии",
                         icon_url=creator.display_avatar)
    else:  # session over
        embed.title = f"Сеанс {name} окончен!"
        embed.colour = Color.red()
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
    def get_voice_channel(user: 'Member'):
        return user.voice.channel if user.voice else None

    @staticmethod
    def fmt(dt: datetime) -> str:
        return dt.strftime('%H:%M %d.%m.%y')

    @staticmethod
    def dt_from_str(s: str) -> datetime:
        return datetime.strptime(s[:19], '%Y-%m-%dT%H:%M:%S')

    def datetime_handler(self, x):
        return self.fmt(self.dt_from_str(x)) if x else '-'

    async def restore_log_session_message(
            self,
            from_date: datetime | None = None,
            to_date: datetime | None = None
    ):
        # FIXME: reuse
        ...

    async def wait_for_session_created(self, session_id: int):
        def check(channel_id: int, _):
            return channel_id == session_id

        result = await self.bot.wait_for(
            'db_session_created',
            check=check,
            timeout=Config.channel_creation_wait_duration,
        )
        # if TimeoutError, then session don't registered by bot.
        # Possible channel is static on server
        return result


class LoggerEventHandlers(DiscordFeaturesMixin, LoggerHelpers):
    def __init__(self, bot):
        super(LoggerEventHandlers, self).__init__(bot)

        # cache stores items only 5 seconds
        self.cache = TTLCache(maxsize=1_000, ttl=5)

        self.vc_status = defaultdict(str)

        self.bot.loop.create_task(self.register_logger_views())
        self.bot.loop.create_task(self.add_members())

    async def register_logger_views(self):
        sessions = await self.db.get_all_sessions()
        for session in sessions:
            view = LoggerView(self.bot, self.datetime_handler)
            self.bot.add_view(view, message_id=session['message_id'])

    async def add_members(self):
        unique_members = set(member
                             for guild in self.bot.guilds
                             for member in guild.members)
        tasks = (
            create_if_not_exists(
                get_url=f'user/{member.id}',
                post_url='user',
                object_={'id': member.id, 'name': member.display_name}
            )
            for member in unique_members
        )
        await asyncio.gather(*tasks)

    async def update_embed_members(self, channel: 'VoiceChannel'):

        if (guild_channels := self.bot.guild_channels.get(
                channel.guild.id)) is None:
            return

        session = await self.db.get_session(channel.id)
        msg_id = session['message_id']

        message = await guild_channels.logger.fetch_message(msg_id)
        members = await self.db.get_session_members(channel.id)
        embed = message.embeds[0]

        embed.set_field_at(
            2,
            name='├ Участники',
            value='└ ' + ', '.join(f'<@{member["id"]}>' for member in members),
            inline=False
        )
        await message.edit(embed=embed)

    async def add_activity_voice_channel(self, channel_id: int, emoji: 'Emoji'):

        if (channel := self.bot.get_channel(channel_id)) is None:
            return

        self.vc_status[channel_id] = str(emoji) + self.vc_status[channel_id]
        await channel.edit(status=self.vc_status[channel_id])

    async def update_activity_icon(
            self,
            channel: Optional['VoiceChannel'],
            app_id: int
    ) -> None:

        session = await self.db.get_session(channel.id)
        app_info = await self.db.get_activity_info(app_id)

        if session and app_info:
            message_id, icon_url = session['message_id'], app_info['icon_url']

            guild_id = channel.guild.id
            if (
            guild_channels := self.bot.guild_channels.get(guild_id)) is None:
                return

            logger_channel = guild_channels.logger

            msg = await logger_channel.fetch_message(message_id)

            embed = msg.embeds[0]
            embed.set_thumbnail(url=icon_url)
            await msg.edit(embed=embed)
            if emoji_db := await self.db.get_activity_emoji(app_id):
                emoji = self.bot.get_emoji(emoji_db['id'])
                self.bot.loop.create_task(msg.add_reaction(emoji))
                self.bot.loop.create_task(
                    self.add_activity_voice_channel(channel_id=channel.id,
                                                    emoji=emoji)
                )

    async def _member_join_channel(
            self,
            member_id: int,
            channel: 'VoiceChannel'
    ):
        async def _add_member():
            try:
                await self.db.session_add_member(channel.id, member_id)
            except ValueError:  # session still not created
                await self.wait_for_session_created(channel.id)
                await _add_member()

            await self.update_embed_members(channel)

        with suppress(TimeoutError):
            await _add_member()
            await self.db.prescence_update(channel_id=channel.id,
                                           member_id=member_id,
                                           begin=now())

    async def _member_abandon_channel(self, member_id: int, channel_id: int):
        await self.db.prescence_update(
            member_id=member_id,
            channel_id=channel_id,
            end=now()
        )


class Logger(LoggerEventHandlers):
    MIN_SESS_DURATION = Config.min_sess_duration  # in seconds

    @Cog.listener()
    async def on_member_join(self, member: 'Member'):
        await self.db.user_create(id=member.id, name=member.display_name)

    @Cog.listener()
    async def on_voice_state_update(
            self,
            member: 'Member',
            before: 'VoiceState',
            after: 'VoiceState'
    ):
        if before.channel == after.channel:  # mute or deaf
            return

        channel = after.channel or before.channel
        try:
            create_channel = self.bot.guild_channels[channel.guild.id].create
        except KeyError:
            return

        if before.channel and before.channel != create_channel:
            await self._member_abandon_channel(member.id, before.channel.id)

        # User join to foreign channel (leave considered the same)
        if after.channel and after.channel != create_channel:
            await self._member_join_channel(member.id, after.channel)

    @Cog.listener()
    async def on_member_join_channel(self, member_id: int,
                                     channel: 'VoiceChannel'):
        await self._member_join_channel(member_id, channel)

    @Cog.listener()
    async def on_db_session_created(self, channel_id: int, message_id: int):
        pass

    @Cog.listener()
    async def on_session_begin(
            self,
            creator: 'Member',
            channel: 'VoiceChannel'
    ):
        begin = now()
        name = channel.name

        embed = create_embed(
            name,
            '└ ' + creator.mention,
            creator,
            self.fmt(begin)
        )

        guild_id = channel.guild.id
        if (guild_channels := self.bot.guild_channels.get(guild_id)) is None:
            return

        logger_channel = guild_channels.logger

        msg = await logger_channel.send(
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

    @Cog.listener()
    async def on_session_over(self, channel: 'VoiceChannel'):
        session = await self.db.get_session(channel.id)
        if session is None:
            return

        guild_id = channel.guild.id
        if (guild_channels := self.bot.guild_channels.get(guild_id)) is None:
            return

        logger_channel = guild_channels.logger

        name, msg_id = session['name'], session['message_id']
        try:
            msg = await logger_channel.fetch_message(msg_id)
        except NotFound:
            return

        begin = self.dt_from_str(session['begin'])
        end = now()
        sess_duration = end - begin

        await self.db.update_leader(channel_id=channel.id, member_id=None,
                                    begin=end)
        await self.db.session_update(channel_id=channel.id, end=end)

        if sess_duration.seconds < Logger.MIN_SESS_DURATION:
            with suppress(NotFound):
                await msg.delete()
            return

        duration_field = f"├ **`{str(sess_duration).split('.')[0]}`**"
        members_mention = (f'<@{member["id"]}>' for member in
                           await self.db.get_session_members(channel.id))
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

    @Cog.listener()
    async def on_activity(
            self,
            before: Optional['Member'],
            after: 'Member',
    ):
        dt = now()

        voice_channel = self.get_voice_channel(after)
        before_app_id = self.get_app_id(before)
        after_app_id = self.get_app_id(after)

        if after_app_id:
            # bot call with same data when registered same user from
            # different guilds

            self.bot.loop.create_task(
                self.db.member_activity(
                    member_id=after.id,
                    id=after_app_id,
                    begin=dt,
                    end=None,
                )
            )

            if voice_channel:
                self.bot.loop.create_task(
                    self.update_activity_icon(voice_channel, after_app_id)
                )

        if before_app_id:
            self.bot.loop.create_task(
                self.db.member_activity(
                    member_id=before.id,
                    id=before_app_id,
                    end=dt
                )
            )

    @Cog.listener()
    async def on_leader_change(
            self,
            channel: 'VoiceChannel',
            leader: 'Member'
    ) -> None:
        session = await self.db.get_session(channel.id)
        if not session:
            return

        guild_id = channel.guild.id
        if (guild_channels := self.bot.guild_channels.get(guild_id)) is None:
            return
        logger_channel = guild_channels.logger

        msg = await logger_channel.fetch_message(session['message_id'])
        name = await self.get_user_sess_name(leader)
        embed: Embed = msg.embeds[0]
        embed.title = constants.active_session(name=name)
        embed.set_field_at(1, name='Текущий лидер', value=leader.mention)

        self.bot.loop.create_task(msg.edit(embed=embed))
        self.bot.loop.create_task(
            self.db.update_leader(
                channel_id=channel.id,
                member_id=leader.id,
                begin=now()
            ),
        )
