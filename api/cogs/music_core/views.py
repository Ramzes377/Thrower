import discord
from typing import Callable


def create_dropdown(placeholder: str, select_options: list, handler: Callable):
    dropdown = Dropdown(placeholder, select_options, handler)
    view = discord.ui.View()
    view.add_item(dropdown)
    return view


class Dropdown(discord.ui.Select):
    def __init__(self, placeholder: str, select_options: list, handler: Callable) -> None:
        self._play = handler
        self._map = {}
        options = []
        for title, query, _ in select_options:
            options.append(discord.SelectOption(label=title))
            self._map[title] = query
        if not options:
            raise AttributeError
        super().__init__(placeholder=placeholder, max_values=None, options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        for val in self.values:
            await interaction.response.send_message(f'{val} будет добавлена в очередь!')
            await self._play(interaction, query=self._map[val])


class PlayerButtonsView(discord.ui.View):
    def __init__(self, pause: Callable, skip: Callable, queue: Callable, favorite: Callable) -> None:
        super().__init__(timeout=None)
        self._pause, self._skip, self._queue, self._favorite = pause, skip, queue, favorite

    @discord.ui.button(label="Play/Pause", style=discord.ButtonStyle.primary, emoji="⏯️")
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._pause(interaction)

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.blurple, emoji="➡️")
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._skip(interaction)

    @discord.ui.button(label="Queue", style=discord.ButtonStyle.blurple)
    async def queue(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._queue(interaction)

    @discord.ui.button(label="Favorite", style=discord.ButtonStyle.blurple, emoji="💙")
    async def favorite(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._favorite(interaction)
