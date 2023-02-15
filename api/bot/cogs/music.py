import discord
from discord import app_commands

from settings import guild
from .music_base import MusicCommandsHandlers


class Music(MusicCommandsHandlers):
    def __init__(self, bot) -> None:
        super(Music, self).__init__(bot)

    @app_commands.command(description='Ссылка или часть названия трека')
    async def play(self, interaction: discord.Interaction, query: str) -> None:
        await self._play(interaction, query)

    @app_commands.command(description='Очередь исполнения')
    async def queue(self, interaction: discord.Interaction) -> None:
        await self._queue(interaction)

    @app_commands.command(description='Быстрый заказ избранных треков')
    async def favorite(self, interaction: discord.Interaction) -> None:
        await self._favorite(interaction)

    @app_commands.command(description='Пауза текущего трека')
    async def pause(self, interaction: discord.Interaction) -> None:
        await self._pause(interaction)

    @app_commands.command(description='Пропуск текущего трека')
    async def skip(self, interaction: discord.Interaction) -> None:
        await self._skip(interaction)

    @app_commands.command(description='Очищает очередь и останавливает исполнение')
    async def stop(self, interaction: discord.Interaction) -> None:
        await self._stop(interaction)


async def setup(bot):
    await bot.add_cog(Music(bot), guilds=[guild])
