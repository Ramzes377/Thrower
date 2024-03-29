import io
import os
from contextlib import suppress
from typing import TYPE_CHECKING

from discord import NotFound, File, ui, ButtonStyle
from jinja2 import FileSystemLoader, Environment
from table2ascii import table2ascii as t2a, PresetStyle

from src.bot.mixins import BaseCogMixin

if TYPE_CHECKING:
    from discord import Guild, Interaction

loader = FileSystemLoader(os.getcwd() + 'static/logger_templates')
env = Environment(loader=loader)


def html_as_bytes(title: str, f_col: str, data: list[tuple[str, str, str]],
                  template: str) -> io.BytesIO:
    template = env.get_template(template)
    html = template.render(title=title, f_column=f_col, data=data)
    return io.BytesIO(html.encode('utf-8'))


async def _response_handle(interaction, string, data, header, column,
                           template='template.html'):
    with suppress(NotFound):
        user = interaction.user
        if len(string) <= 2000:
            await user.send(f"```{string}```", delete_after=2 * 60)
        else:
            bts = html_as_bytes(header, column, data, template)
            await user.send(file=File(bts, filename=f'{header}.html'),
                            delete_after=2 * 60)
        await interaction.response.send_message(
            f'Успешно отправлена информация', ephemeral=True, delete_after=5)


class LoggerView(ui.View, BaseCogMixin):
    def __init__(self, bot, format_handler) -> None:
        ui.View.__init__(self, timeout=None)
        BaseCogMixin.__init__(self, bot, sub_cog=True)
        self._fmt = format_handler

    async def format_data(
            self,
            response: list[dict],
            header: str,
            col: str,
            guild: 'Guild',
            activity_flag: bool = False
    ) -> tuple[str, list]:
        data, body = [], []
        for row in response:
            user_id, begin, end = (row['member_id'], self._fmt(row['begin']),
                                   self._fmt(row['end']))
            user = guild.get_member(user_id)
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

    @ui.button(style=ButtonStyle.primary, emoji="👑",
               custom_id='logger_view:leadership', )
    async def leadership(self, interaction: 'Interaction', _) -> None:
        header, column = 'Лидеры сессии', 'Лидер'
        leadership = await self.db.get_session_leadership(
            interaction.message.id
        )
        as_str, data = await self.format_data(leadership, header, column,
                                              interaction.guild)
        await _response_handle(interaction, as_str, data, header, column)

    @ui.button(style=ButtonStyle.blurple, emoji="🎮",
               custom_id='logger_view:activities')
    async def activities(self, interaction: 'Interaction', _) -> None:
        header, column = 'Активности сессии', 'Активность'
        activities = await self.db.get_session_activities(
            interaction.message.id
        )
        as_str, data = await self.format_data(activities, header, column,
                                              interaction.guild,
                                              activity_flag=True)
        await _response_handle(interaction, as_str, data, header, column,
                               'activity_template.html')

    @ui.button(style=ButtonStyle.blurple, emoji="🚶",
               custom_id='logger_view:prescence')
    async def prescence(self, interaction: 'Interaction', _) -> None:
        header, column = 'Участники сессии', 'Участник'
        prescence = await self.db.get_session_prescence(interaction.message.id)
        as_str, data = await self.format_data(prescence, header, column, interaction.guild)
        await _response_handle(interaction, as_str, data, header, column)
