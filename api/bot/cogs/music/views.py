from typing import Callable

import discord


def create_view(placeholder: str, select_options: list[dict], guild_id: int, handler: Callable):
    dropdown = Dropdown(placeholder, select_options, guild_id, handler)
    view = discord.ui.View()
    view.add_item(dropdown)
    return view


class Dropdown(discord.ui.Select):
    def __init__(self,
                 placeholder: str,
                 select_options: list[dict],
                 guild_id: int,
                 handler: Callable) -> None:
        self._play = handler
        self._guild_id = guild_id
        self._map = {}
        options = []
        for option in select_options:
            title, query = option['title'], option['query']
            options.append(discord.SelectOption(label=title))
            self._map[title] = query
        super().__init__(placeholder=placeholder, max_values=None, options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        for title in self.values:
            await interaction.response.send_message(f'{title} будет добавлена в очередь!', delete_after=15)
            interaction.guild_id = self._guild_id
            await self._play(interaction, query=self._map[title])


class PlayerButtonsView(discord.ui.View):
    def __init__(self, pause: Callable, skip: Callable, queue: Callable, favorite: Callable) -> None:
        super().__init__(timeout=None)
        self._pause, self._skip, self._queue, self._favorite = pause, skip, queue, favorite

    @discord.ui.button(style=discord.ButtonStyle.grey, emoji="⏯️")
    async def pause(self, interaction: discord.Interaction, _) -> None:
        await self._pause(interaction)

    @discord.ui.button(style=discord.ButtonStyle.grey, emoji="⏭️")
    async def skip(self, interaction: discord.Interaction, _) -> None:
        await self._skip(interaction)

    @discord.ui.button(style=discord.ButtonStyle.grey, emoji="🇶")
    async def queue(self, interaction: discord.Interaction, _) -> None:
        await self._queue(interaction)

    @discord.ui.button(style=discord.ButtonStyle.gray, emoji="💝")
    async def favorite(self, interaction: discord.Interaction, _) -> None:
        await self._favorite(interaction)
