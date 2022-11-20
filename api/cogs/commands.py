import asyncio
import datetime
import discord
from discord.ext import commands

from time import time

from .tools.mixins import BaseCogMixin, commands, DiscordFeaturesMixin
from .tools.utils import get_app_id, user_is_playing, send_removable_message


class Commands(BaseCogMixin, DiscordFeaturesMixin):
    CLEAR_CONNECTION_PERIOD: int = 5 * 60   # seconds

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, _):
        if user_is_playing(before):
            await self.write_played_time(before)

    @commands.command(aliases=['a', 'act'])
    async def activity(self, ctx: commands.Context):
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
            embed = discord.Embed(title=f"Обработан ваш запрос по игре {role.name}", color=role.color)
            seconds = await self.execute_sql(
                f"SELECT COALESCE(seconds, 0) FROM UserActivities WHERE role_id = {role.id} and user_id = {member.id}")
            if seconds and seconds[0]:
                ingame_time = datetime.timedelta(seconds=seconds[0])
                embed.add_field(name='В игре вы провели', value=f"{str(ingame_time).split('.')[0]}", inline=False)
            else:
                embed.add_field(name='Вы не играли в эту игру или Discord не смог это обнаружить',
                                value='Если вам нужна эта функция,'
                                      'то зайдите в Настройки пользователя/Игровая активность/Отображать '
                                      'в статусе игру в которую сейчас играете',
                                inline=False)
            icon_url = await self.execute_sql(
                f'''SELECT icon_url FROM CreatedRoles join ActivitiesINFO using(app_id) WHERE role_id = {role.id}''')
            if icon_url:
                embed.set_thumbnail(url=icon_url[0])
            bot = channel.guild.get_member(self.bot.user.id)
            embed.set_footer(text='Великий бот - ' + bot.display_name, icon_url=bot.avatar)
            embed.description = 'Это сообщение автоматически удалится через минуту'
            message = await member.send(embed=embed)
            sended_messages.append(message)

        await asyncio.sleep(20)
        try:
            for message in sended_messages:
                await message.delete()
            await ctx.message.delete()
        except discord.errors.NotFound:
            pass

    @commands.command(aliases=['gr'])
    async def give_role(self, ctx: commands.Context):
        """Дает пользователю ИГРОВУЮ роль!
        Введите
        !give_role @роль чтобы получить роль!
        или
        !give_role @роль, @роль, ...
        чтобы получить сразу несколько ролей!"""
        member = ctx.message.author
        requested_roles = ctx.update_msg.role_mentions
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
        await ctx.update_msg.delete()

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx: commands.Context, messages_count: int = 0):
        """
        Удаляет последние message_count сообщений
           Example: !clear 10
           Только для ролей с правом удаления сообщений.
        """
        channel = ctx.message.channel
        async for message in channel.history(limit=messages_count + 1):
            try:
                await message.delete()
            except:
                pass

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def clear_connections(self, ctx: commands.Context):
        await self._clear_connections()
        await ctx.message.delete()

    async def get_gamerole_time(self, user_id: int, app_id: int):
        return await self.execute_sql(f'''SELECT cr.role_id, COALESCE(ua.seconds, 0) seconds
                                                FROM CreatedRoles as cr
                                                    left JOIN UserActivities as ua on 
                                                        cr.role_id = ua.role_id 
                                                        and user_id = {user_id}
                                                WHERE cr.app_id = {app_id}''')

    async def write_played_time(self, before: discord.Member):
        app_id, _ = get_app_id(before)
        role_id, seconds = await self.get_gamerole_time(before.id, app_id)
        if not (before.activity and before.activity.start):
            return
        sess_duration = int(time() - before.activity.start.timestamp())
        await self.execute_sql(
            f"INSERT INTO UserActivities (role_id, user_id, seconds) VALUES ({role_id}, {before.id}, 0) ON CONFLICT (role_id, user_id) DO NOTHING",
            f'UPDATE UserActivities SET seconds = {seconds + sess_duration} WHERE role_id = {role_id} and user_id = {before.id}'
        )

    async def _clear_connections(self):
        await self.bot.db.clear()
        print("Successfully cleared db connections!")

    async def clear_connections_loop(self):
        while True:
            try:
                await self._clear_connections()
                await asyncio.sleep(Commands.CLEAR_CONNECTION_PERIOD)
            except AttributeError:
                pass


async def setup(bot):
    _commands = Commands(bot)
    await bot.add_cog(_commands)
    bot.loop.create_task(_commands.clear_connections_loop())