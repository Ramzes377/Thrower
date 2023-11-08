import asyncio
from asyncio import get_event_loop, AbstractEventLoop, new_event_loop
from queue import Queue
from typing import Coroutine


class DeferredTasksProcessor:

    def __init__(self,
                 sleep_seconds: int = 30,
                 event_loop: AbstractEventLoop | None = None):

        self._unordered_items: list[Coroutine] = []
        self._ordered_items: Queue[Coroutine] = Queue()

        try:
            self.event_loop = event_loop or get_event_loop()
        except RuntimeError:
            self.event_loop = new_event_loop()

        self.sleep_seconds = sleep_seconds

    async def add(self, coro: Coroutine, is_ordered: bool = True) -> None:
        """ Add item to deferred tasks execution container. """
        if is_ordered:
            self._ordered_items.put(coro)
        else:
            self._unordered_items.append(coro)

    async def _run_unordered(self) -> None:
        await asyncio.gather(*self._unordered_items)
        self._unordered_items.clear()

    async def _run_ordered(self) -> None:
        while not self._ordered_items.empty():
            coro = self._ordered_items.get()
            try:
                await coro
            except Exception as e:
                print(e)
                continue

    async def start(self) -> None:
        while True:
            await asyncio.gather(
                self._run_unordered(),
                self._run_ordered()
            )
            await asyncio.sleep(self.sleep_seconds)
