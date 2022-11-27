import io
from typing import Callable

import discord
from discord.ext import commands
from jinja2 import FileSystemLoader, Environment
from table2ascii import table2ascii as t2a, PresetStyle

from api.core.logger.log_detail import get_leaders_list, get_activities_list, get_prescence_list
from api.mixins import ExecuteMixin
from api.misc import fmt, dt_from_str

loader = FileSystemLoader('api/core/logger/templates')
env = Environment(loader=loader)
template = env.get_template('template.html')


def format_date(s: str) -> str:
    return fmt(dt_from_str(s))


def html_as_bytes(title: str, f_col: str, data: list[tuple[str, str, str]]) -> io.BytesIO:
    html = template.render(title=title, f_column=f_col, data=data)
    return io.BytesIO(html.encode('utf-8'))


def format_members(getter: Callable, bot: commands.Bot, message_id: int, header: str, col: str) -> tuple[str, list]:
    data = []
    body = []
    for user_id, begin, end in getter(message_id):
        user = bot.guilds[0].get_member(user_id)
        name = f'''<a href="https://discordapp.com/users/{user_id}/"> {user.display_name} </a>'''
        begin = format_date(begin)
        end = '-' if end is None else format_date(end)
        data.append((name, begin, end))
        body.append((user.display_name, begin, end))

    as_str = t2a(
        header=[col, "Время начала", "Время окончания"],
        body=body,
        style=PresetStyle.thin_compact
    )
    return header + as_str, data


class LoggerView(discord.ui.View, ExecuteMixin):
    def __init__(self, bot) -> None:
        super().__init__(timeout=None)
        self.bot = bot

    async def format_activities(self, message_id: int) -> str:
        data = []
        body = []
        for app_id, member_id, begin, end in get_activities_list(message_id):
            role_id = await self.execute_sql(f"SELECT role_id FROM CreatedRoles WHERE app_id = {app_id}")
            role = self.bot.guilds[0].get_role(role_id)
            user = self.bot.guilds[0].get_member(member_id)
            member_repr = f'''<a href="https://discordapp.com/users/{user.id}/"> {user.display_name} </a>'''
            name = role.name
            if role.display_icon:
                name = f'<a>{name}  <img src={role.display_icon} height="60"></a>'
            begin = format_date(begin)
            end = '-' if end is None else format_date(end)
            data.append((name, member_repr, begin, end))
            body.append((role.name, user.display_name, begin, end))

        as_str = t2a(
            header=["Активность", "Участник", "Время начала", "Время окончания"],
            body=body,
            style=PresetStyle.thin_compact
        )

        return 'Активности сессии\n' + as_str, data

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="👑", custom_id='logger_view:leadership', )
    async def leadership(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        header = 'Лидеры сессии\n'
        col_name = 'Лидер'
        as_str, data = format_members(get_leaders_list, self.bot, interaction.message.id, header, col_name)
        if len(as_str) <= 2000:
            await interaction.response.send_message(f"```{as_str}```", delete_after=30)
        else:
            bts = html_as_bytes(title=header, f_col=col_name, data=data)
            await interaction.response.send_message(file=discord.File(bts, filename='leaders.html'), delete_after=30)

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="🎮", custom_id='logger_view:activities')
    async def activities(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        as_str, data = await self.format_activities(interaction.message.id)
        if len(as_str) <= 2000:
            await interaction.response.send_message(f"```{as_str}```", delete_after=30)
        else:
            bts = html_as_bytes(title='Активности сессии', f_col='Активность', data=data)
            await interaction.response.send_message(file=discord.File(bts, filename='leaders.html'), delete_after=30)

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="🚶", custom_id='logger_view:prescence')
    async def prescence(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        header = 'Участники сессии\n'
        col_name = 'Участник'
        as_str, data = format_members(get_prescence_list, self.bot, interaction.message.id, header, col_name)
        if len(as_str) <= 2000:
            await interaction.response.send_message(f"```{as_str}```", delete_after=30)
        else:
            bts = html_as_bytes(title=header, f_col=col_name, data=data)
            await interaction.response.send_message(file=discord.File(bts, filename='leaders.html'), delete_after=30)
