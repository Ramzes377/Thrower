import io
import os

import discord
from jinja2 import FileSystemLoader, Environment
from table2ascii import table2ascii as t2a, PresetStyle

from api.bot.mixins import BaseCogMixin
from api.bot.misc import fmt, dt_from_str

loader = FileSystemLoader(os.getcwd() + '/api/bot/logger/templates')
env = Environment(loader=loader)
template = env.get_template('template.html')


def fmt_date(s: str) -> str:
    return fmt(dt_from_str(s)) if s else '-'


def html_as_bytes(title: str, f_col: str, data: list[tuple[str, str, str]]) -> io.BytesIO:
    html = template.render(title=title, f_column=f_col, data=data)
    return io.BytesIO(html.encode('utf-8'))


async def _response_handle(interaction, string, data, header, column):
    if len(string) <= 2000:
        await interaction.response.send_message(f"```{string}```", delete_after=30)
    else:
        bts = html_as_bytes(title=header, f_col=column, data=data)
        await interaction.response.send_message(file=discord.File(bts, filename=f'{header}.html'), delete_after=30)


class LoggerView(discord.ui.View, BaseCogMixin):
    def __init__(self, bot) -> None:
        discord.ui.View.__init__(self, timeout=None)
        BaseCogMixin.__init__(self, bot, silent=True)

    def format_data(self, response: list[dict], header: str, col: str, activity_flag: bool = False) -> tuple[str, list]:
        data, body = [], []
        for row in response:
            user_id, begin, end = row['member_id'], fmt_date(row['begin']), fmt_date(row['end'])
            user = self.bot.guilds[0].get_member(user_id)
            url = f'''<a href="https://discordapp.com/users/{user_id}/"> {user.display_name} </a>'''
            if not activity_flag:
                data.append((url, begin, end))
                body.append((user.display_name, begin, end))
            else:
                activity = self._client.get(f'v1/activity/{row["id"]}/info/').json()
                name = activity['app_name']
                data.append((name, url, begin, end))
                body.append((name, user.display_name, begin, end))

        headers = [col, "Время начала", "Время окончания"]
        if activity_flag:
            headers.insert(0, "Активность")

        as_str = t2a(
            header=headers,
            body=body,
            style=PresetStyle.thin_compact
        )
        return f'\t\t{header}\n' + as_str, data

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="👑", custom_id='logger_view:leadership', )
    async def leadership(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        header, column = 'Лидеры сессии', 'Лидер'
        leadership = self._client.get(f'v1/session/{interaction.message.id}/leadership').json()
        as_str, data = self.format_data(leadership, header, column)
        await _response_handle(interaction, as_str, data, header, column)

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="🎮", custom_id='logger_view:activities')
    async def activities(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        header, column = 'Активности сессии', 'Активность'
        activities = self._client.get(f'v1/session/activities/by_msg/{interaction.message.id}').json()
        as_str, data = self.format_data(activities, header, column, activity_flag=True)
        await _response_handle(interaction, as_str, data, header, column)

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="🚶", custom_id='logger_view:prescence')
    async def prescence(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        header, column = 'Участники сессии', 'Участник'
        prescence = self._client.get(f'v1/prescence/by_msg/{interaction.message.id}').json()
        as_str, data = self.format_data(prescence, header, column)
        await _response_handle(interaction, as_str, data, header, column)
