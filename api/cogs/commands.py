import asyncio
import datetime
import discord

from time import time

from .tools.base_cog import BaseCog, commands
from .tools.utils import get_app_id, user_is_playing


async def send_removable_message(ctx, message, delay=5):
    message = await ctx.send(message)
    await asyncio.sleep(delay)
    await message.delete()


class Commands(BaseCog):

    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        await self.game_statistics(before, after)

    @commands.command(aliases=['a', 'act'])
    async def activity(self, ctx):
        """
        Дает пользователю время в игре у соответствующей игре роли!
           Введите !activity @роль или Введите !activity @роль @роль . . .
           Если вам необходимо отображение количества проведённого времени в игре,
           то для этого необходимо чтобы было включено отображение игровой активности в настройках Discord!
        """
        member = ctx.message.author
        channel = ctx.message.channel
        requested_games = ctx.message.role_mentions

        if len(requested_games) == 0:
            await send_removable_message(ctx, 'Отсутствуют упоминания игровых ролей! Введите !help activity', 20)
            await ctx.message.delete()
            return

        sended_messages = []
        for role in requested_games:
            seconds = await self.execute_sql(f"SELECT seconds FROM UserActivities WHERE role_id = {role.id}")
            if seconds:
                ingame_time = datetime.timedelta(seconds=seconds[0])
                embed = discord.Embed(title=f"Обработан ваш запрос по игре {role.name}", color=role.color)
                if ingame_time:
                    embed.add_field(name='В игре вы провели', value=f"{str(ingame_time).split('.')[0]}",
                                    inline=False)
                else:
                    embed.add_field(name='Вы не играли в эту игру или Discord не смог это обнаружить',
                                    value='Если вам нужна эта функция,'
                                          'то зайдите в Настройки пользователя/Игровая активность/Отображать '
                                          'в статусе игру в которую сейчас играете',
                                    inline=False)

                icon_url = await self.execute_sql(f'''SELECT icon_url FROM ActivitiesINFO 
                                            WHERE app_id = (SELECT app_id FROM CreatedRoles WHERE role_id = {role.id})''')
                if icon_url:
                    embed.set_thumbnail(url=icon_url[0])

                bot = channel.guild.get_member(self.bot.user.id)
                embed.set_footer(text='Великий бот - ' + bot.display_name, icon_url=bot.avatar)
                embed.description = 'Это сообщение автоматически удалится через минуту'

                message = await member.send(embed=embed)
                sended_messages.append(message)

        await asyncio.sleep(60)
        try:
            for message in sended_messages:
                await message.delete()
            await ctx.message.delete()
        except discord.errors.NotFound:
            pass

    @commands.command(aliases=['gr'])
    async def give_role(self, ctx):
        '''Дает пользователю ИГРОВУЮ роль!
        Введите
        !give_role @роль чтобы получить роль!
        или
        !give_role @роль, @роль, ...
        чтобы получить сразу несколько ролей!'''
        member = ctx.message.author
        requested_roles = ctx.message.role_mentions

        if len(requested_roles) == 0:
            await send_removable_message(ctx, 'Отсутствуют упоминания ролей! Введите !help give_role.', 20)
            await ctx.message.delete()
            return

        sended_messages = []
        for role in requested_roles:
            role_exist = await self.execute_sql(f"SELECT count(*) FROM CreatedRoles WHERE role_id = {role.id}")
            if role_exist:  # it's created role
                if role not in member.roles:  # member hasn't these role
                    await member.add_roles(role)
                    message = await send_removable_message(ctx, f'Успешно добавлена роль {role.mention}!', 60)
                else:  # member already have these role
                    message = await send_removable_message(ctx, f'У вас уже есть роль {role.mention}!', 20)
            else:  # wrong role
                message = await send_removable_message(ctx, f'{role.mention} не относится к игровым ролям!', 20)

            sended_messages.append(message)

        await asyncio.sleep(20)
        for message in sended_messages:
            await message.delete()
        await ctx.message.delete()

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, messages_count=0):
        '''Удаляет последние message_count сообщений
           Example: !clear 10
           Только для ролей с правом удаления сообщений.'''
        channel = ctx.message.channel
        async for message in channel.history(limit=messages_count + 1):
            await message.delete()

    async def get_gamerole_time(self, user_id, app_id):
        gamerole_time = await self.execute_sql(
            f'''SELECT role_id, COALESCE(seconds, 0) 
                    FROM CreatedRoles
                        LEFT JOIN UserActivities USING(role_id)
                WHERE user_id = {user_id} AND app_id = {app_id}''')
        return gamerole_time

    async def game_statistics(self, before, after):
        if user_is_playing(after):
            app_id, _ = get_app_id(after)
            gamerole_time = await self.get_gamerole_time(after.id, app_id)
            if gamerole_time:
                _, seconds = gamerole_time
                if not seconds:
                    await self.execute_sql(
                        f"INSERT INTO UserActivities (user_id, app_id, seconds) VALUES ({after.id}, {app_id}, {0})")
        if user_is_playing(before):
            try:
                app_id, _ = get_app_id(before)
                gamerole_time = await self.get_gamerole_time(before.id, app_id)
                if gamerole_time:
                    role_id, seconds = gamerole_time
                    sess_duration = int(time() - before.activity.start.timestamp())
                    await self.execute_sql(
                        f"UPDATE UserActivities SET seconds = {seconds + sess_duration} WHERE user_id = {before.id} AND role_id = {role_id}")
            except AttributeError:
                pass


async def setup(bot):
    await bot.add_cog(Commands(bot))