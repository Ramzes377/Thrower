import asyncio
from asyncio import AbstractEventLoop
from asyncio import Queue as AsyncQueue
from typing import Coroutine, Callable

from fastapi import HTTPException

from utils import discord_logger


class DeferredTasksProcessor:
    _event_loop = None

    def __init__(self, sleep_seconds: int = 30):

        self._unordered_items: list[Coroutine] = []
        self._ordered_items: AsyncQueue[tuple[Callable, dict, dict]] = AsyncQueue()

        self.sleep_seconds = sleep_seconds

    @property
    def event_loop(self):
        return self._event_loop

    @event_loop.setter
    def event_loop(self, loop: AbstractEventLoop):
        self._event_loop = loop
        self._ordered_items = AsyncQueue()

    async def add(self,
                  coro_fabric: Callable,
                  coro_kwargs: dict,
                  repeat_on_failure: bool,
                  is_ordered: bool = True) -> None:
        """ Add item to deferred tasks execution container. """

        if is_ordered:
            await self._ordered_items.put(
                (coro_fabric, coro_kwargs,
                 dict(repeat_on_failure=repeat_on_failure))
            )
        else:
            coro: Coroutine = coro_fabric(**coro_kwargs)
            self._unordered_items.append(coro)

    async def _run_unordered(self) -> None:
        await asyncio.gather(*self._unordered_items)
        self._unordered_items.clear()

    async def _run_ordered(self) -> None:
        while not self._ordered_items.empty():
            discord_logger.debug(f'Current tasks num: {self._ordered_items.qsize()}')

            coro_fabric, coro_kwargs, kw = await self._ordered_items.get()
            coro: Coroutine = coro_fabric(**coro_kwargs)
            try:
                discord_logger.debug(f"Execute coro: {coro}")
                resp = await coro
                discord_logger.debug(f"Response: {resp}")
            except HTTPException as e:
                discord_logger.debug(e.detail)
                if kw['repeat_on_failure']:
                    await self.add(coro_fabric, coro_kwargs, **kw)
                continue
            except Exception as e:
                discord_logger.debug(e)
                if kw['repeat_on_failure']:
                    await self.add(coro_fabric, coro_kwargs, **kw)
                continue

    async def start(self, loop: AbstractEventLoop) -> None:
        self.event_loop = loop

        while True:
            await asyncio.gather(
                self._run_unordered(),
                self._run_ordered()
            )
            await asyncio.sleep(self.sleep_seconds)
