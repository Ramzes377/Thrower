from contextlib import suppress
from typing import Callable, TYPE_CHECKING

from discord import ui, SelectOption, InteractionResponded, ButtonStyle

if TYPE_CHECKING:
    from discord import Interaction


def create_view(
        placeholder: str,
        select_options: list[dict],
        guild_id: int,
        handler: Callable
) -> ui.View:

    dropdown = Dropdown(placeholder, select_options, guild_id, handler)
    view = ui.View()
    view.add_item(dropdown)
    return view


class Dropdown(ui.Select):
    def __init__(
            self,
            placeholder: str,
            select_options: list[dict],
            guild_id: int,
            handler: Callable
    ) -> None:
        self._play = handler
        self._guild_id = guild_id
        self._map = {}
        options = []
        for option in select_options:
            title, query = option['title'], option['query']
            options.append(SelectOption(label=title))
            self._map[title] = query
        super().__init__(placeholder=placeholder,
                         max_values=len(select_options),
                         options=options)

    async def callback(self, interaction: 'Interaction') -> None:
        for title in self.values:
            with suppress(InteractionResponded):
                await interaction.response.send_message(   # noqa
                    f'{title} будет добавлена в очередь!',
                    delete_after=15
                )
            interaction.guild_id = self._guild_id
            await self._play(interaction, query=self._map[title])


class PlayerButtonsView(ui.View):
    def __init__(
            self,
            pause: Callable,
            skip: Callable,
            queue: Callable,
            favorite: Callable
    ) -> None:
        super().__init__(timeout=None)
        self._pause, self._skip, self._queue, self._favorite = pause, skip, queue, favorite

    @ui.button(style=ButtonStyle.grey, emoji="⏯️")
    async def pause(self, interaction: 'Interaction', _) -> None:
        await self._pause(interaction)

    @ui.button(style=ButtonStyle.grey, emoji="⏭️")
    async def skip(self, interaction: 'Interaction', _) -> None:
        await self._skip(interaction)

    @ui.button(style=ButtonStyle.grey, emoji="🇶")
    async def queue(self, interaction: 'Interaction', _) -> None:
        await self._queue(interaction)

    @ui.button(style=ButtonStyle.gray, emoji="💝")
    async def favorite(self, interaction: 'Interaction', _) -> None:
        await self._favorite(interaction)
