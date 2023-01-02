import datetime

import discord
from discord import app_commands
from discord.ext import commands, tasks

from api.bot.mixins import BaseCogMixin, DiscordFeaturesMixin
from api.bot.misc import get_app_id, user_is_playing, now
from api.bot.vars import guild_id, tzMoscow

CLEAR_CONNECTIONS_PERIOD = 5 * 60  # seconds


class Commands(DiscordFeaturesMixin):

    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    async def sync(self, interaction: discord.Interaction) -> None:
        print('here')
        await interaction.response.send_message(await self.bot.tree.sync(guild=interaction.guild),
                                                ephemeral=True, delete_after=30)

    @app_commands.command(description='Удаление n предшевствующих сообщений')
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, n: int = 0) -> None:
        await interaction.response.send_message(f'Будет удалено {n} сообщений!',
                                                ephemeral=True, delete_after=30)
        async for message in interaction.channel.history(limit=n):
            try:
                await message.delete()
            except:
                pass

    @app_commands.command(description='Показывает зарегистрированное время в игре у соответствующей игровой роли!')
    async def played(self, interaction: discord.Interaction, role_mention: str):
        """
         Дает пользователю зарегистрированное время в игре у соответствующей игре роли! Введите /activity @роль
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
            return

        embed = discord.Embed(title=f"Обработан ваш запрос по игре {role.name}", color=role.color)

        data = await self.request(f'user/{interaction.user.id}/activities/duration/{role.id}')
        if self._object_exist(data):
            ingame_time = datetime.timedelta(seconds=data['seconds'])
            embed.add_field(name='В игре вы провели', value=f"{str(ingame_time).split('.')[0]}", inline=False)
        else:
            embed.add_field(name='Вы не играли в эту игру или Discord не смог это обнаружить',
                            value='Если вам нужна эта функция,'
                                  'то зайдите в Настройки пользователя/Игровая активность/Отображать '
                                  'в статусе игру в которую сейчас играете',
                            inline=False)
        embed.set_footer(text='Великий бот - ' + self.bot.user.display_name, icon_url=self.bot.user.avatar)
        await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=30)


async def setup(bot):
    await bot.add_cog(Commands(bot), guilds=[discord.Object(id=guild_id)])
