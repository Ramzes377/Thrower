import datetime
import discord
from random import choice

from .tools.base_cog import BaseCog
from .tools.utils import flatten, time_format, user_is_playing, get_app_id, session_id, urls, zone_Moscow


class Logger(BaseCog):
    MIN_SESS_DURATION = 5 * 60  # in seconds

    async def log_activity(self, user, user_channel):
        if not user_is_playing(user):
            return

        app_id, is_real = get_app_id(user)
        associate_role = await self.execute_sql(f"SELECT role_id FROM CreatedRoles WHERE app_id = {app_id}")
        if is_real:
            try:
                await self.execute_sql(f"INSERT INTO SessionActivities (channel_id, associate_role) VALUES ({user_channel.id}, {associate_role[0]})")
                msg = await self.update_activity_icon(app_id, user_channel.id)
                if msg:
                    await self.log_msg_add_activities(msg, associate_role)
            except:  # record already exist not duplicate session activities
                pass

    async def update_activity_icon(self, app_id, channel_id):
        icon_data = await self.execute_sql(
            f"SELECT message_id FROM LoggerSessions WHERE channel_id = {channel_id}",
            f'SELECT icon_url FROM ActivitiesINFO WHERE app_id  = {app_id}'
        )
        if icon_data:
            message_id, thumbnail_url = icon_data
            msg = await self.bot.logger_channel.fetch_message(message_id[0])
            msg_embed = msg.embeds[0]
            msg_embed.set_thumbnail(url=thumbnail_url[0])
            await msg.edit(embed=msg_embed)
            return msg

    async def session_begin_msg(self, creator, channel):
        day_of_year, is_leap_year = session_id()
        past_sessions_counter, current_sessions_counter = await self.execute_sql(
            f"SELECT past_sessions_counter, current_sessions_counter FROM SessionCounters WHERE current_day = {day_of_year}"
        )
        sess_id = f'№ {1 + past_sessions_counter + current_sessions_counter} | {day_of_year}/{366 if is_leap_year else 365}'
        cur_time = datetime.datetime.now(tz=zone_Moscow)

        embed = discord.Embed(title=f"{creator.display_name} начал сессию {sess_id}", color=discord.Color.green())
        embed.add_field(name='├ Сессия активна', value=f'├ [ВАЖНО!]({choice(urls)})', inline=False)
        embed.add_field(name=f'├ Время начала', value=f'└ **`{time_format(cur_time)}`**', inline=True)
        embed.add_field(name='Текущий лидер', value=f'{creator.mention}', inline=True)
        creator = channel.guild.get_member(creator.id)
        embed.set_footer(text=creator.display_name + " - Создатель сессии", icon_url=creator.avatar)
        msg = await self.bot.logger_channel.send(embed=embed)

        await self.execute_sql(
            f"UPDATE SessionCounters SET current_sessions_counter = {current_sessions_counter + 1} WHERE current_day = {day_of_year}",
            f"INSERT INTO LoggerSessions (channel_id, creator_id, start_day, sess_repr, message_id) VALUES ({channel.id}, {creator.id}, {day_of_year}, '{sess_id}', {msg.id})"
        )
        await self.log_activity(creator, channel)

    async def session_over_msg(self, channel):
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
            end_time = datetime.datetime.now(tz=zone_Moscow)
            sess_duration = end_time - start_time

            if sess_duration.seconds > Logger.MIN_SESS_DURATION:
                _, session_members, associated_roles = await self.execute_sql(
                    f"UPDATE SessionCounters SET past_sessions_counter = {past_sessions_counter + 1} WHERE current_day = {start_day}",
                    f"SELECT member_id FROM SessionMembers WHERE channel_id = {channel.id}",
                    f"SELECT associate_role FROM SessionActivities WHERE channel_id = {channel.id}", fetch_all=True)
                users_ids = set(flatten(session_members))
                roles_ids = set(flatten(associated_roles))

                embed_obj = discord.Embed(title=f"Сессия {sess_repr} окончена!", color=discord.Color.red())
                embed_obj.description = f'├ [ВАЖНО!]({choice(urls)})'
                embed_obj.add_field(name=f'├ Время начала', value=f'├ **`{time_format(start_time)}`**', inline=True)
                embed_obj.add_field(name='Время окончания', value=f'**`{time_format(end_time)}`**')
                embed_obj.add_field(name='├ Продолжительность', value=f"├ **`{str(sess_duration).split('.')[0]}`**",
                                    inline=False)
                embed_obj.add_field(name='├ Участники', value='└ ' + ', '.join((f'<@{id}>' for id in users_ids)),
                                    inline=False)
                thumbnail_url = msg.embeds[0].thumbnail.url
                if thumbnail_url:
                    embed_obj.set_thumbnail(url=thumbnail_url)
                embed_obj.set_footer(text=msg.embeds[0].footer.text, icon_url=msg.embeds[0].footer.icon_url)
                await msg.edit(embed=embed_obj)
                await self.log_msg_add_activities(msg, roles_ids)
            else:
                await msg.delete()
        except Exception as e:
            pass
        finally:
            await self.execute_sql(f"DELETE FROM CreatedSessions WHERE channel_id = {channel.id}",
                                   f"DELETE FROM SessionMembers WHERE channel_id = {channel.id}",
                                   f"DELETE FROM SessionActivities WHERE channel_id = {channel.id}",
                                   f"DELETE FROM LoggerSessions WHERE channel_id = {channel.id}")

    async def log_msg_add_activities(self, msg, roles_ids):
        for role_id in roles_ids:
            emoji_id = await self.execute_sql(f'''SELECT emoji_id FROM 
                                                    CreatedRoles  
                                                        JOIN CreatedEmoji 
                                                            on CreatedRoles.role_id = CreatedEmoji.role_id
                                                    WHERE CreatedRoles.role_id = {role_id}''')
            if emoji_id:
                emoji = self.bot.get_emoji(emoji_id[0])
                if emoji:
                    await msg.add_reaction(emoji)


async def setup(bot):
    await bot.add_cog(Logger(bot))
