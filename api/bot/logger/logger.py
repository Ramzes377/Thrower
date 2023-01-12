import discord

from api.bot.logger.dbevents import DBEvents
from api.bot.logger.views import LoggerView
from api.bot.mixins import DiscordFeaturesMixin
from api.bot.misc import fmt, user_is_playing, get_app_id, tzMoscow, now, get_voice_channel


class Logger(DiscordFeaturesMixin):
    MIN_SESS_DURATION = 5 * 60  # in seconds

    def __init__(self, bot):
        super(Logger, self).__init__(bot, silent=True)
        self.events = DBEvents(bot)
        self.bot.loop.create_task(self.register_logger_views())

    async def register_logger_views(self):
        sessions: list[dict] = await self.request('session/')
        for session in sessions:
            self.bot.add_view(LoggerView(self.bot), message_id=session['message_id'])

    async def session_begin(self, creator_id: int, channel: discord.VoiceChannel):
        begin = now()
        creator = channel.guild.get_member(creator_id)
        name = channel.name

        embed = (
            discord.Embed(title=f"Активен сеанс: {name}", color=discord.Color.green())
            .add_field(name=f'├ Время начала', value=f'├ **`{fmt(begin)}`**')
            .add_field(name='Текущий лидер', value=creator.mention)
            .add_field(name='├ Участники', value='└ ' + f'<@{creator.id}>', inline=False)
            .set_footer(text=creator.display_name + " - Создатель сессии", icon_url=creator.display_avatar)
        )

        msg = await self.bot.logger_channel.send(embed=embed, view=LoggerView(self.bot))
        await self.events.session_update(creator_id=creator.id, channel_id=channel.id, message_id=msg.id, begin=begin,
                                         name=name)
        await self.events.session_prescence(channel_id=channel.id, member_id=creator.id, begin=begin)
        await self.log_activity(None, creator)

    async def session_over(self, channel_id: int):
        session = await self.get_session(channel_id)
        if session is None:
            return

        sess_name, msg_id = session['name'], session['message_id']
        try:
            msg = await self.bot.logger_channel.fetch_message(msg_id)
        except:
            return

        begin = msg.created_at.astimezone(tzMoscow)
        end = now()
        sess_duration = end - begin

        if sess_duration.seconds < Logger.MIN_SESS_DURATION:
            await msg.delete()
            await self.events.session_update(channel_id=channel_id, end=now())
            return

        duration_field = f"├ **`{str(sess_duration).split('.')[0]}`**"
        members_field = '└ ' + ', '.join(
            f'<@{member["id"]}>' for member in await self.request(f'session/{channel_id}/members')
        )

        embed = (
            discord.Embed(title=f"Сеанс {sess_name} окончен!", color=discord.Color.red())
            .add_field(name=f'├ Время начала', value=f'├ **`{fmt(begin)}`**')
            .add_field(name='Время окончания', value=f'**`{fmt(end)}`**')
            .add_field(name='├ Продолжительность', value=duration_field, inline=False)
            .add_field(name='├ Участники', value=members_field, inline=False)
            .set_footer(text=msg.embeds[0].footer.text, icon_url=msg.embeds[0].footer.icon_url)
            .set_thumbnail(url=msg.embeds[0].thumbnail.url)
        )

        await msg.edit(embed=embed)
        json = {'channel_id': channel_id, 'member_id': None, 'end': end.strftime('%Y-%m-%dT%H:%M:%S')}
        await self.request('leadership/', 'post', json=json)
        await self.events.session_update(channel_id=channel_id, end=now())

    async def update_sess_name(self, msg_id: int, name: str):
        msg = await self.bot.logger_channel.fetch_message(msg_id)
        dct = msg.embeds[0].to_dict()
        dct['title'] = f"Активен сеанс: {name}"
        embed = discord.Embed.from_dict(dct)
        await msg.edit(embed=embed)

    async def update_leader(self, channel_id: int, leader_id: int):
        session = await self.get_session(channel_id)
        if not self.exist(session):
            return

        msg = await self.bot.logger_channel.fetch_message(session['message_id'])
        embed = msg.embeds[0]
        embed.set_field_at(1, name='Текущий лидер', value=f'<@{leader_id}>')
        await msg.edit(embed=embed)
        await self.events.session_update(channel_id=channel_id, member_id=leader_id, end=now())

    async def update_embed_members(self, session_id: int):
        members = await self.request(f'session/{session_id}/members')
        session = await self.get_session(session_id)
        message = await self.bot.logger_channel.fetch_message(session['message_id'])
        embed = message.embeds[0]
        embed.set_field_at(2, name='├ Участники',
                           value='└ ' + ', '.join(f'<@{member["id"]}>' for member in members),
                           inline=False)
        await message.edit(embed=embed)

    async def update_activity_icon(self, channel_id: int, app_id: int):
        session = await self.get_session(channel_id)
        app_info = await self.request(f'activity/{app_id}/info')
        if self.exist(session) and self.exist(app_info):
            message_id, thumbnail_url = session['message_id'], app_info['icon_url']
            msg = await self.bot.logger_channel.fetch_message(message_id)
            embed = msg.embeds[0]
            embed.set_thumbnail(url=thumbnail_url)
            await msg.edit(embed=embed)

            emoji = await self.request(f'activity/{app_id}/emoji')
            if self.exist(emoji):
                await msg.add_reaction(self.bot.get_emoji(emoji['id']))

    async def log_activity(self, before: discord.Member | None, after: discord.Member):
        timestamp = now()
        voice_channel = get_voice_channel(after)

        before_app_id, before_is_real = get_app_id(before)
        after_app_id, after_is_real = get_app_id(after)

        after_familiar = user_is_playing(after) and after_is_real
        before_familiar = before is not None and user_is_playing(before) and before_is_real

        if after_familiar:
            await self.events.member_activity(member_id=after.id, id=after_app_id, begin=timestamp, end=None)
            if voice_channel is not None:  # logging activities of user in channel
                await self.update_activity_icon(voice_channel.id, after_app_id)

        if before_familiar:
            await self.events.member_activity(member_id=before.id, id=before_app_id, end=timestamp)

    async def log_member_join(self, user_id: int, channel_id: int):
        try:
            await self.request(f'session/{channel_id}/members/{user_id}', 'post')
            await self.update_embed_members(channel_id)  # add new member to logging message
        except:
            await self.events.session_prescence(channel_id=channel_id, member_id=user_id, begin=now())

    async def log_member_abandon(self, user_id: int, channel_id: int):
        await self.events.session_prescence(member_id=user_id, channel_id=channel_id, end=now())
