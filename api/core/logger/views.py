from typing import Callable, Generator

import discord

from api.core.logger.log_detail import get_leaders_list, get_activities_list, get_prescence_list

from api.tools.mixins import ConnectionMixin
from api.tools.misc import fmt, dt_from_str


def format_date(s: str) -> str:
    return fmt(dt_from_str(s))


def format_members(getter: Callable, message_id: int) -> Generator:
    return ((f"<@{l[0]}>", format_date(l[1]), format_date(l[2]) if l[2] is not None else "#" * 10) for l in
            getter(message_id))


def create_embed(title: str, first_column: str):
    embed = discord.Embed(title=title)
    embed.add_field(name=first_column, value='\u200b', inline=True)
    embed.add_field(name="Время начала", value='\u200b', inline=True)
    embed.add_field(name="Время окончания", value='\u200b', inline=True)
    return embed


def set_embed_row(embed, *row):
    for field in row:
        embed.add_field(name='\u200b', value=field, inline=True)


class LoggerView(discord.ui.View, ConnectionMixin):
    def __init__(self, bot) -> None:
        super().__init__(timeout=None)
        self.bot = bot

    async def format_activities(self, message_id: int) -> str:
        res = []
        for id, begin, end in get_activities_list(message_id):
            role_id = await self.execute_sql(f"SELECT role_id FROM CreatedRoles WHERE app_id = {id}")
            end = format_date(end) if end else '#' * 10
            res.append((f'<@&{role_id}>' if role_id else 'Deleted role', format_date(begin), end))
        return res

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="👑", custom_id='logger_view:leadership')
    async def leadership(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        embed = create_embed(title='Лидеры сессии', first_column='Лидер')
        for member_id, begin_date, end_date in format_members(get_leaders_list, interaction.message.id):
            set_embed_row(embed, member_id, begin_date, end_date)
        await interaction.response.send_message(embed=embed, ephemeral=False, delete_after=30)

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="🎮", custom_id='logger_view:activities')
    async def activities(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        embed = create_embed(title='Активности сессии', first_column='Активность')
        for activity_id, begin_date, end_date in await self.format_activities(interaction.message.id):
            set_embed_row(embed, activity_id, begin_date, end_date)
        await interaction.response.send_message(embed=embed, ephemeral=False, delete_after=30)

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="🚶", custom_id='logger_view:prescence')
    async def prescence(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        embed = create_embed(title='Участники сессии', first_column='Участник')
        for member_id, begin_date, end_date in format_members(get_prescence_list, interaction.message.id):
            set_embed_row(embed, member_id, begin_date, end_date)
        await interaction.response.send_message(embed=embed, ephemeral=False, delete_after=30)
