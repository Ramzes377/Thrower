import io
import os

import discord
from jinja2 import FileSystemLoader, Environment
from table2ascii import table2ascii as t2a, PresetStyle

from api.bot.mixins import BaseCogMixin
from api.bot.misc import fmt, dt_from_str

loader = FileSystemLoader(os.getcwd() + '/api/bot/logger/templates')
env = Environment(loader=loader)


def fmt_date(s: str) -> str:
    return fmt(dt_from_str(s)) if s else '-'


def html_as_bytes(title: str, f_col: str, data: list[tuple[str, str, str]], template: str) -> io.BytesIO:
    template = env.get_template(template)
    html = template.render(title=title, f_column=f_col, data=data)
    return io.BytesIO(html.encode('utf-8'))


async def _response_handle(interaction, string, data, header, column, template='template.html'):
    try:
        user = interaction.user
        if len(string) <= 2000:
            await user.send(f"```{string}```", delete_after=2 * 60)
        else:
            bts = html_as_bytes(header, column, data, template)
            await user.send(file=discord.File(bts, filename=f'{header}.html'), delete_after=2 * 60)
        await interaction.response.send_message(f'Успешно отправлена информация', ephemeral=True, delete_after=5)
    except discord.errors.NotFound:
        pass


class LoggerView(discord.ui.View, BaseCogMixin):
    def __init__(self, bot) -> None:
        discord.ui.View.__init__(self, timeout=None)
        BaseCogMixin.__init__(self, bot, silent=True)

    async def format_data(self, response: list[dict], header: str,
                          col: str, activity_flag: bool = False) -> tuple[str, list]:
        data, body = [], []
        for row in response:
            user_id, begin, end = row['member_id'], fmt_date(row['begin']), fmt_date(row['end'])
            user = self.bot.guilds[0].get_member(user_id)
            url = f'''<a href="https://discordapp.com/users/{user_id}/"> {user.display_name} </a>'''
            if not activity_flag:
                data.append((url, begin, end))
                body.append((user.display_name, begin, end))
            else:
                activity = await self.db.get_activity_info(row["id"])
                name = activity['app_name']
                data.append((name, url, begin, end))
                body.append((name, user.display_name, begin, end))

        headers = [col, "Время начала", "Время окончания"]
        if activity_flag:
            headers.insert(1, "Участник")

        as_str = t2a(
            header=headers,
            body=body,
            style=PresetStyle.thin_compact
        )
        return f'\t\t{header}\n' + as_str, data

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="👑", custom_id='logger_view:leadership', )
    async def leadership(self, interaction: discord.Interaction, _) -> None:
        header, column = 'Лидеры сессии', 'Лидер'
        leadership = await self.db.get_session_leadership(interaction.message.id)
        as_str, data = await self.format_data(leadership, header, column)
        await _response_handle(interaction, as_str, data, header, column)

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="🎮", custom_id='logger_view:activities')
    async def activities(self, interaction: discord.Interaction, _) -> None:
        header, column = 'Активности сессии', 'Активность'
        activities = await self.db.get_session_activities(interaction.message.id)
        as_str, data = await self.format_data(activities, header, column, activity_flag=True)
        await _response_handle(interaction, as_str, data, header, column, 'activity_template.html')

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="🚶", custom_id='logger_view:prescence')
    async def prescence(self, interaction: discord.Interaction, _) -> None:
        header, column = 'Участники сессии', 'Участник'
        prescence =  await self.db.get_session_prescence(interaction.message.id)
        as_str, data = await self.format_data(prescence, header, column)
        await _response_handle(interaction, as_str, data, header, column)
