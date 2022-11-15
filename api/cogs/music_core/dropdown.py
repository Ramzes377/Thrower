import discord
from typing import Callable


def create_dropdown(placeholder: str, select_options: list, handlers: list[Callable] = None):
    dropdown = Dropdown(placeholder, select_options, handlers)
    view = discord.ui.View()
    view.add_item(dropdown)
    return view


class Dropdown(discord.ui.Select):
    def __init__(self, placeholder: str, select_options: list, handlers: list[Callable]):
        self._ensure, self._play = handlers
        self._map = {}
        options = []
        for title, query, _ in select_options:
            options.append(discord.SelectOption(label=title))
            self._map[title] = query
        if not options:
            raise AttributeError
        super().__init__(placeholder=placeholder, max_values=None, options=options)

    async def callback(self, interaction: discord.Interaction):
        for val in self.values:
            await interaction.response.send_message(f'{val} будет добавлена в очередь!')
            await self._ensure()
            await self._play(query=self._map[val])
