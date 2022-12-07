import discord
from hashlib import blake2b

from api.bot.logger.dbevents import dbEvents
from api.bot.logger.views import LoggerView
from api.bot.mixins import DiscordFeaturesMixin
from api.bot.misc import fmt, user_is_playing, get_app_id, tzMoscow, now, get_voice_channel


class Logger(DiscordFeaturesMixin):
    MIN_SESS_DURATION = 5 * 60  # in seconds

    def __init__(self, bot):
        super(Logger, self).__init__(bot, silent=True)
        self.events = dbEvents(bot)
        self.register_logger_views()

    def register_logger_views(self):
        sessions: list[dict] = self._client.get(f'v1/session/all/').json()
        for session in sessions:
            self.bot.add_view(LoggerView(self.bot), message_id=session['message_id'])

    async def session_begin(self, creator: discord.Member, channel: discord.VoiceChannel):
        sess_name = f'#{blake2b(str(channel.id).encode(), digest_size=4).hexdigest()}'
        begin = now()
        embed = discord.Embed(title=f"{creator.display_name} начал сессию {sess_name}", color=discord.Color.green())
        embed.add_field(name=f'├ Время начала', value=f'├ **`{fmt(begin)}`**')
        embed.add_field(name='Текущий лидер', value=f'{creator.mention}')
        embed.add_field(name='├ Участники', value='└ ' + f'<@{creator.id}>', inline=False)
        creator = channel.guild.get_member(creator.id)
        embed.set_footer(text=creator.display_name + " - Создатель сессии", icon_url=creator.display_avatar)
        msg = await self.bot.logger_channel.send(embed=embed, view=LoggerView(self.bot))
        await self.log_activity(None, creator)
        self.events.session_update(creator_id=creator.id, channel_id=channel.id, message_id=msg.id,
                                   begin=begin, name=sess_name)
        self.events.session_prescence(channel_id=channel.id, member_id=creator.id, begin=begin)

    async def session_over(self, channel: discord.VoiceChannel):
        session = self.get_session(channel.id)
        if session is None:
            return

        sess_name, msg_id = session['name'], session['message_id']
        msg = await self.bot.logger_channel.fetch_message(msg_id)

        begin = msg.created_at.astimezone(tzMoscow)
        end = now()
        sess_duration = end - begin

        if sess_duration.seconds < Logger.MIN_SESS_DURATION:
            await msg.delete()
            self.events.session_update(channel_id=channel.id, end=now())
            return

        embed = discord.Embed(title=f"Сессия {sess_name} окончена!", color=discord.Color.red())
        embed.description = f'├ '
        embed.add_field(name=f'├ Время начала', value=f'├ **`{fmt(begin)}`**', inline=True)
        embed.add_field(name='Время окончания', value=f'**`{fmt(end)}`**')
        embed.add_field(name='├ Продолжительность', value=f"├ **`{str(sess_duration).split('.')[0]}`**",
                        inline=False)
        embed.add_field(name='├ Участники', value='└ ', inline=False)
        thumbnail_url = msg.embeds[0].thumbnail.url
        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)
        embed.set_footer(text=msg.embeds[0].footer.text, icon_url=msg.embeds[0].footer.icon_url)
        await msg.edit(embed=embed)
        await self.update_embed_members(session)
        self._client.post(f'v1/leadership', json={'channel_id': channel.id, 'member_id': None, 'end': end.strftime('%Y-%m-%dT%H:%M:%S')})
        self.events.session_update(channel_id=channel.id, end=now())

    async def update_leader(self, channel_id: discord.VoiceChannel, leader: discord.Member):
        try:
            session = self.get_session(channel_id)
            if not self._object_exist(session):
                return

            msg = await self.bot.logger_channel.fetch_message(session['message_id'])
            embed = msg.embeds[0]
            embed.set_field_at(2, name='Текущий лидер', value=leader.mention)
            await msg.edit(embed=embed)
            self.events.session_update(channel_id=channel_id, member_id=leader.id, end=now())
        except (discord.errors.NotFound, TypeError):
            pass

    async def update_embed_members(self, session: dict):
        try:
            members: list[dict] = self._client.get(f'v1/session/{session["channel_id"]}/members/').json()
            message = await self.bot.logger_channel.fetch_message(session['message_id'])
            embed = message.embeds[0]
            embed.set_field_at(3, name='├ Участники',
                               value='└ ' + ', '.join(f'<@{member["id"]}>' for member in members),
                               inline=False)
            await message.edit(embed=embed)
        except:
            pass

    async def update_activity_icon(self, channel_id: int, app_id: int):
        session = self.get_session(channel_id)
        app_info = self._client.get(f'v1/activity/{app_id}/info/').json()
        if self._object_exist(session) and self._object_exist(app_info):
            message_id, thumbnail_url = session['message_id'], app_info['icon_url']
            msg = await self.bot.logger_channel.fetch_message(message_id)
            embed = msg.embeds[0]
            embed.set_thumbnail(url=thumbnail_url)
            await msg.edit(embed=embed)

            emoji = self._client.get(f'v1/activity/{app_id}/emoji/').json()
            if self._object_exist(emoji):
                await msg.add_reaction(self.bot.get_emoji(emoji['id']))

    async def log_activity(self, before: discord.Member, after: discord.Member):
        voice_channel = get_voice_channel(after)

        before_app_id, before_is_real = get_app_id(before)
        after_app_id, after_is_real = get_app_id(after)

        after_familiar = user_is_playing(after) and after_is_real
        before_familiar = before is not None and user_is_playing(before) and before_is_real

        if not before_familiar and not after_familiar:
            return

        if after_familiar:
            begin = after.activity.start.astimezone(tzMoscow)
            channel_id = voice_channel.id if voice_channel else None
            self.events.member_activity(channel_id, after_app_id,
                                        member_id=after.id, id=after_app_id, begin=begin, end=None)
            if voice_channel is not None:  # logging activities from ANY user in these channel
                await self.update_activity_icon(voice_channel.id, after_app_id)

        if before_familiar:
            self.events.member_activity(None, None, member_id=before.id, id=before_app_id, end=now())

    async def log_member_join(self, user: discord.Member, channel: discord.VoiceChannel):
        self._client.post(f'v1/session/{channel.id}/members/{user.id}')
        self.events.session_prescence(channel_id=channel.id, member_id=user.id, begin=now())
        await self.update_embed_members(channel.id)  # add new member to logging message

    async def log_member_abandon(self, user: discord.Member, channel: discord.VoiceChannel):
        self.events.session_prescence(channel_id=channel.id, member_id=user.id, end=now())
