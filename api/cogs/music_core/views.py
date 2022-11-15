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


class PlayerButtonsView(discord.ui.View):
    def __init__(self, pause_handler: Callable, skip_handle: Callable):
        super().__init__()
        self._paused = False
        self._pause, self._skip = pause_handler, skip_handle

    @discord.ui.button(label="Play/Pause", style=discord.ButtonStyle.primary, emoji="⏯️")
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._paused = not self._paused
        await self._pause(self._paused)
        try:
            await interaction.response.send_message('', ephemeral=True)
        except discord.errors.HTTPException:
            pass

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.blurple, emoji="➡️")
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._skip()
        try:
            await interaction.response.send_message('', ephemeral=True)
        except discord.errors.HTTPException:
            pass
