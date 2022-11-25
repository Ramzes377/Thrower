import discord
from random import choice

from api.core.logger.log_detail import leadership_begin, leadership_end, member_join, member_leave, \
    register_detailed_log, get_detailed_msgs, log_activity_begin, log_activity_end, message_from_channel
from api.core.logger.views import LoggerView
from api.mixins import ExecuteMixin
from api.misc import fmt, user_is_playing, get_app_id, session_id, urls, zone_Moscow, now


def register_logger_views(bot):
    for msg_id, *_ in get_detailed_msgs():
        bot.add_view(LoggerView(bot), message_id=msg_id)


class Logger(ExecuteMixin):
    MIN_SESS_DURATION = 5 * 60  # in seconds

    def __init__(self, bot):
        super(Logger, self).__init__()
        self.bot = bot
        register_logger_views(bot)

    async def log_activity(self, before: discord.Member, after: discord.Member, channel: discord.VoiceChannel):
        before_app_id, before_is_real = get_app_id(before)
        after_app_id, after_is_real = get_app_id(after)

        after_familiar = user_is_playing(after) and after_is_real
        before_familiar = before is not None and user_is_playing(before) and before_is_real

        if not before_familiar and not after_familiar:
            return

        if after_familiar:
            msg = await self.update_activity_icon(channel.id, after_app_id)
            log_activity_begin(msg.id, after_app_id, after.activity.start.astimezone(zone_Moscow))
            role_id = await self.execute_sql(f"SELECT role_id FROM CreatedRoles WHERE app_id = {after_app_id}")
            try:
                await self.execute_sql(
                    f"INSERT INTO SessionActivities (channel_id, role_id) VALUES ({channel.id}, {role_id})")
                if msg:
                    await self.add_activity(msg, role_id)
            except:  # record already exist not duplicate session activities
                pass

        if before_familiar:
            try:
                msg_id = message_from_channel(channel.id)[0]
                log_activity_end(msg_id, before_app_id, before.activity.start.astimezone(zone_Moscow), now())
            except TypeError:
                pass

    async def update_activity_icon(self, channel_id: int, app_id: int):
        icon_data = await self.execute_sql(f"SELECT message_id FROM LoggerSessions WHERE channel_id = {channel_id}",
                                           f'SELECT icon_url FROM ActivitiesINFO WHERE app_id = {app_id}')
        if icon_data:
            message_id, thumbnail_url = icon_data
            msg = await self.bot.logger_channel.fetch_message(message_id)
            msg_embed = msg.embeds[0]
            msg_embed.set_thumbnail(url=thumbnail_url)
            await msg.edit(embed=msg_embed)
            return msg

    async def session_begin(self, creator: discord.Member, channel: discord.VoiceChannel):
        day_of_year, is_leap_year = session_id()
        past_sessions_counter, current_sessions_counter = await self.execute_sql(
            f"SELECT past_sessions_counter, current_sessions_counter FROM SessionCounters WHERE current_day = {day_of_year}"
        )
        sess_id = f'№ {1 + past_sessions_counter + current_sessions_counter} | {day_of_year}/{366 if is_leap_year else 365}'
        cur_time = now()

        embed = discord.Embed(title=f"{creator.display_name} начал сессию {sess_id}", color=discord.Color.green())
        embed.add_field(name='├ Сессия активна', value=f'├ [ВАЖНО!]({choice(urls)})', inline=False)
        embed.add_field(name=f'├ Время начала', value=f'├ **`{fmt(cur_time)}`**')
        embed.add_field(name='Текущий лидер', value=f'{creator.mention}')
        embed.add_field(name='├ Участники', value='└ ' + f'<@{creator.id}>', inline=False)
        creator = channel.guild.get_member(creator.id)
        embed.set_footer(text=creator.display_name + " - Создатель сессии", icon_url=creator.display_avatar)
        msg = await self.bot.logger_channel.send(embed=embed, view=LoggerView(self.bot))

        await self.execute_sql(
            f"UPDATE SessionCounters SET current_sessions_counter = {current_sessions_counter + 1} WHERE current_day = {day_of_year}",
            f"INSERT INTO LoggerSessions (channel_id, creator_id, start_day, sess_repr, message_id) VALUES ({channel.id}, {creator.id}, {day_of_year}, '{sess_id}', {msg.id})"
        )
        await self.log_activity(None, creator, channel)
        register_detailed_log(msg.id, channel.id)
        start_time = msg.created_at.astimezone(zone_Moscow)
        leadership_begin(msg.id, creator.id, start_time)
        member_join(msg.id, creator.id, start_time)

    async def change_leader(self, prev_leader: discord.Member, leader: discord.Member,
                            channel_id: discord.VoiceChannel):
        try:
            message_id = message_from_channel(channel_id)[0]
            msg = await self.bot.logger_channel.fetch_message(message_id)
            embed = msg.embeds[0]
            embed.set_field_at(2, name='Текущий лидер', value=leader.mention)
            await msg.edit(embed=embed)
            t0 = now()
            leadership_end(msg.id, prev_leader.id, t0)
            leadership_begin(msg.id, leader.id, t0)
        except (discord.errors.NotFound, TypeError):
            pass

    async def update_embed_members(self, channel: discord.VoiceChannel):
        try:
            message_id, *member_ids = await self.execute_sql(
                f"SELECT message_id FROM LoggerSessions WHERE channel_id = {channel.id}",
                f"SELECT member_id FROM SessionMembers WHERE channel_id = {channel.id}",
                fetch_all=True)
            msg = await self.bot.logger_channel.fetch_message(message_id)
            embed = msg.embeds[0]
            embed.set_field_at(3, name='├ Участники', value='└ ' + ', '.join((f'<@{id}>' for id in member_ids)),
                               inline=False)
            await msg.edit(embed=embed)
        except:
            pass

    async def add_activity(self, msg: discord.Message, role_id: int):
        emoji_id = await self.execute_sql(f'''SELECT emoji_id FROM 
                                                CreatedRoles JOIN CreatedEmoji 
                                                    on CreatedRoles.role_id = CreatedEmoji.role_id
                                                WHERE CreatedRoles.role_id = {role_id}''')
        await msg.add_reaction(self.bot.get_emoji(emoji_id))

    async def session_over(self, channel: discord.VoiceChannel):
        try:
            creator_id, start_day, sess_repr, message_id = \
                await self.execute_sql(
                    f"SELECT creator_id, start_day, sess_repr, message_id FROM LoggerSessions WHERE channel_id = {channel.id}"
                )
            msg = await self.bot.logger_channel.fetch_message(message_id)
            past_sessions_counter, current_sessions_counter = await self.execute_sql(
                f"SELECT past_sessions_counter, current_sessions_counter FROM SessionCounters WHERE current_day = {start_day}")
            await self.execute_sql(
                f"UPDATE SessionCounters SET current_sessions_counter = {current_sessions_counter - 1} WHERE current_day = {start_day}")
            start_time = msg.created_at.astimezone(zone_Moscow)
            end_time = now()
            sess_duration = end_time - start_time

            if sess_duration.seconds > Logger.MIN_SESS_DURATION:
                _, *roles_ids = await self.execute_sql(
                    f"UPDATE SessionCounters SET past_sessions_counter = {past_sessions_counter + 1} WHERE current_day = {start_day}",
                    f"SELECT role_id FROM SessionActivities WHERE channel_id = {channel.id}", fetch_all=True)

                embed = discord.Embed(title=f"Сессия {sess_repr} окончена!", color=discord.Color.red())
                embed.description = f'├ [ВАЖНО!]({choice(urls)})'
                embed.add_field(name=f'├ Время начала', value=f'├ **`{fmt(start_time)}`**', inline=True)
                embed.add_field(name='Время окончания', value=f'**`{fmt(end_time)}`**')
                embed.add_field(name='├ Продолжительность', value=f"├ **`{str(sess_duration).split('.')[0]}`**",
                                inline=False)
                embed.add_field(name='├ Участники', value='└ ', inline=False)
                thumbnail_url = msg.embeds[0].thumbnail.url
                if thumbnail_url:
                    embed.set_thumbnail(url=thumbnail_url)
                embed.set_footer(text=msg.embeds[0].footer.text, icon_url=msg.embeds[0].footer.icon_url)
                leader_id = int(msg.embeds[0].fields[2].value[2:-1])
                leadership_end(message_id, leader_id, end_time)
                member_leave(message_id, leader_id, end_time)
                await msg.edit(embed=embed)
                await self.update_embed_members(channel)
                await self.add_activity(msg, roles_ids)

            else:
                await msg.delete()
        except:
            pass
        finally:
            await self.execute_sql(
                f'''DELETE FROM CreatedSessions WHERE channel_id = {channel.id}; 
                    DELETE FROM SessionActivities WHERE channel_id = {channel.id}'''
            )

    async def log_member_join(self, user: discord.Member, channel: discord.VoiceChannel):
        try:
            try:
                msg_id = message_from_channel(channel.id)[0]
                member_join(msg_id, user.id, now())
            except TypeError:
                pass
            await self.execute_sql(
                f'INSERT INTO SessionMembers (channel_id, member_id) VALUES ({channel.id}, {user.id})')
            # add new member to logging message
            await self.update_embed_members(channel=channel)
        except:
            pass

    async def log_member_abandon(self, user: discord.Member, channel: discord.VoiceChannel):
        try:
            message_id = message_from_channel(channel.id)[0]
            member_leave(message_id, user.id, now())
        except TypeError:
            pass

