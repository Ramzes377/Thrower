import asyncio
import datetime
import discord
from discord import app_commands
from discord.ext import commands

from time import time

from api.mixins import BaseCogMixin, DiscordFeaturesMixin
from api.misc import get_app_id, user_is_playing, guild_id


class Commands(BaseCogMixin, DiscordFeaturesMixin):
    CLEAR_CONNECTIONS_PERIOD: int = 5 * 60  # seconds

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, _):
        if user_is_playing(before):
            await self.write_played_time(before)

    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    async def sync(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(await self.bot.tree.sync(guild=interaction.guild),
                                                ephemeral=True, delete_after=30)

    @app_commands.command(description='Показывает зарегистрированное время в игре у соответствующей игровой роли!')
    async def activity(self, interaction: discord.Interaction, role_mention: str):
        """
        Дает пользователю время в игре у соответствующей игре роли! Введите /activity @роль
           Если вам необходимо отображение количества проведённого времени в игре,
           то для этого необходимо чтобы было включено отображение игровой активности в настройках Discord.
        """
        guild = self.bot.guilds[0]
        try:
            role_id = int(role_mention[3:-1])
            role = guild.get_role(role_id)
        except:
            await interaction.response.send_message('Неверный формат упоминания игровой роли!', ephemeral=True,
                                                    delete_after=30)

        embed = discord.Embed(title=f"Обработан ваш запрос по игре {role.name}", color=role.color)
        seconds = await self.execute_sql(
            f"SELECT COALESCE(seconds, 0) FROM UserActivities WHERE role_id = {role.id} and user_id = {interaction.user.id}")
        if seconds:
            ingame_time = datetime.timedelta(seconds=seconds)
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
            embed.set_thumbnail(url=icon_url)
        embed.set_footer(text='Великий бот - ' + self.bot.user.display_name, icon_url=self.bot.user.avatar)
        await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=30)

    @app_commands.command(description='Удаление n предшевствующих сообщений')
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, n: int = 0) -> None:
        await interaction.response.send_message(f'Будет удалено {n} сообщений!',
                                                ephemeral=True, delete_after=30)
        async for message in interaction.channel.history(limit=n + 1):
            try:
                await message.delete()
            except:
                pass

    @app_commands.command(description='Попытка закрытия открытых соединений к бд')
    @app_commands.checks.has_permissions(administrator=True)
    async def clear_connections(self, interaction: discord.Interaction):
        await self.bot.db.clear()
        await interaction.response.send_message(f'Очищены открытые соединения', ephemeral=True, delete_after=30)

    async def get_gamerole_time(self, user_id: int, app_id: int):
        return await self.execute_sql(f'''SELECT cr.role_id, COALESCE(ua.seconds, 0) seconds
                                                FROM CreatedRoles as cr
                                                    left JOIN UserActivities as ua on 
                                                        cr.role_id = ua.role_id 
                                                        and user_id = {user_id}
                                                WHERE cr.app_id = {app_id}''', fetch_all=False)

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

    async def clear_connections_loop(self):
        while True:
            try:
                await self.bot.db.clear()
                await asyncio.sleep(Commands.CLEAR_CONNECTIONS_PERIOD)
            except AttributeError:
                pass


async def setup(bot):
    _commands = Commands(bot)
    await bot.add_cog(_commands, guilds=[discord.Object(id=guild_id)])
    bot.loop.create_task(_commands.clear_connections_loop())
