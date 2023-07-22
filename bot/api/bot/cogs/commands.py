import asyncio
import datetime
from contextlib import suppress

import discord
from discord import app_commands

from ..mixins import DiscordFeaturesMixin


class Commands(DiscordFeaturesMixin):

    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    async def sync(self, interaction: discord.Interaction) -> None:
        sync = await self.bot.tree.sync(guild=interaction.guild)
        await interaction.response.send_message(
            sync, ephemeral=True, delete_after=30
        )

    @app_commands.command(description='Удаление n предшествующих сообщений')
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, n: int = 0) -> None:
        await interaction.response.send_message(f'Будет удалено {n} сообщений!',
                                                ephemeral=True, delete_after=30)
        async for message in interaction.channel.history(limit=n):
            with suppress(discord.NotFound):
                await message.delete()

    @app_commands.command(description='Очистка переписки с этим ботом')
    async def clear_private(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            f'Начата очистка переписки . . .',
            ephemeral=True, delete_after=30
        )
        await interaction.user.send('!')
        counter = 0
        async for message in interaction.user.dm_channel.history(limit=None):
            with suppress(discord.NotFound):
                await message.delete()
                counter += 1
        await interaction.response.send_message(
            f'Успешно удалено {counter} сообщений!',
            ephemeral=True,
            delete_after=30
        )

    @app_commands.command(
        description='Показывает зарегистрированное время в игре у '
                    'соответствующей игровой роли!'
    )
    async def played(self, interaction: discord.Interaction, role_mention: str):
        guild = interaction.guild
        try:
            role_id = int(role_mention[3:-1])
            role = guild.get_role(role_id)
        except ValueError:
            await interaction.response.send_message(
                'Неверный формат упоминания игровой роли!',
                ephemeral=True,
                delete_after=30
            )
            return

        embed = discord.Embed(title=f"Запрос по игре {role.name}",
                              color=role.color)

        data = await self.db.get_activity_duration(interaction.user.id, role.id)
        if data:
            game_time = datetime.timedelta(seconds=data['seconds'])
            embed.add_field(name='Зарегистрировано в игре ',
                            value=f"{str(game_time).split('.')[0]}",
                            inline=False)
        else:
            embed.add_field(
                name='Вы не играли в эту игру или Discord не смог это обнаружить',
                value='Если вам нужна эта функция,'
                      'то зайдите в Настройки пользователя/Игровая активность/Отображать '
                      'в статусе игру в которую сейчас играете',
                inline=False)
        embed.set_footer(text='Великий бот - ' + self.bot.user.display_name,
                         icon_url=self.bot.user.avatar)
        await interaction.response.send_message(embed=embed, ephemeral=True,
                                                delete_after=30)

    async def update_sess_name(self, channel_id: int, name: str):
        session = await self.db.session_update(channel_id=channel_id, name=name)
        await self.db.user_update(id=session["leader_id"],
                                  default_sess_name=session['name'])

        msg = await self.bot.channel.logger.fetch_message(session['message_id'])
        dct = msg.embeds[0].to_dict()
        dct['title'] = f"Активен сеанс: {name}"
        embed = discord.Embed.from_dict(dct)
        await msg.edit(embed=embed)

    @staticmethod
    async def rename_channel(channel: discord.VoiceChannel, name: str):
        coro = channel.edit(name=name)
        with suppress(asyncio.TimeoutError):
            await asyncio.wait_for(coro, timeout=300)

    @app_commands.command(
        description='Устанавливает стандартное название вашей сессии')
    async def session_name(self, interaction: discord.Interaction, name: str):
        await self.db.user_update(id=interaction.user.id,
                                  default_sess_name=name)
        msg = f'Успешно установлено стандартное название сессии: {name}'
        await interaction.response.send_message(msg, ephemeral=True,
                                                delete_after=30)
        channel = await self.get_user_channel(interaction.user.id)
        if channel:
            await self.rename_channel(channel, name)
            await self.update_sess_name(channel.id, name)


async def setup(bot):
    try:
        from config import Config
    except ModuleNotFoundError:
        from bot.config import Config
    await bot.add_cog(Commands(bot), guilds=[Config.GUILD])
