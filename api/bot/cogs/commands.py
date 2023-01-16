import datetime

import discord
from discord import app_commands

from api.bot.mixins import BasicRequests
from settings import envs

CLEAR_CONNECTIONS_PERIOD = 5 * 60  # seconds


class Commands(BasicRequests):

    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    async def sync(self, interaction: discord.Interaction) -> None:
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

    @app_commands.command(description='Очистка переписки с этим ботом')
    async def clear_private(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f'Начата очистка переписки . . .',
                                                ephemeral=True, delete_after=30)
        await interaction.user.send('!')
        counter = 0
        async for message in interaction.user.dm_channel.history(limit=None):
            try:
                await message.delete()
                counter += 1
            except:
                pass
        await interaction.response.send_message(f'Успешно удалено {counter} сообщений!',
                                                ephemeral=True, delete_after=30)

    @app_commands.command(description='Показывает зарегистрированное время в игре у соответствующей игровой роли!')
    async def played(self, interaction: discord.Interaction, role_mention: str):
        guild = self.bot.guilds[0]
        try:
            role_id = int(role_mention[3:-1])
            role = guild.get_role(role_id)
        except:
            await interaction.response.send_message('Неверный формат упоминания игровой роли!', ephemeral=True,
                                                    delete_after=30)
            return

        embed = discord.Embed(title=f"Запрос по игре {role.name}", color=role.color)

        data = await self.get_activity_duration(interaction.user.id, role.id)
        if self.exist(data):
            ingame_time = datetime.timedelta(seconds=data['seconds'])
            embed.add_field(name='Зарегистрировано в игре ', value=f"{str(ingame_time).split('.')[0]}", inline=False)
        else:
            embed.add_field(name='Вы не играли в эту игру или Discord не смог это обнаружить',
                            value='Если вам нужна эта функция,'
                                  'то зайдите в Настройки пользователя/Игровая активность/Отображать '
                                  'в статусе игру в которую сейчас играете',
                            inline=False)
        embed.set_footer(text='Великий бот - ' + self.bot.user.display_name, icon_url=self.bot.user.avatar)
        await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=30)


async def setup(bot):
    guild = discord.Object(id=envs['guild_id'])
    await bot.add_cog(Commands(bot), guilds=[guild])
