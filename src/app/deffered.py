from asyncio import Queue as AsyncQueue, sleep, gather
from typing import TYPE_CHECKING

from fastapi import HTTPException

from src.constants import constants
from src.utils import logger

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop
    from src.utils import CoroItem


class DeferredTasksProcessor:
    repeat_attempts = 5
    _event_loop = None

    def __init__(self, sleep_seconds: int = 30):

        self._unordered_items: AsyncQueue['CoroItem'] = AsyncQueue()
        self._ordered_items: AsyncQueue['CoroItem'] = AsyncQueue()

        self.sleep_seconds = sleep_seconds

    @property
    def event_loop(self):
        return self._event_loop

    @event_loop.setter
    def event_loop(self, loop: 'AbstractEventLoop'):
        self._event_loop = loop
        self._ordered_items = AsyncQueue()

    async def add(self,
                  coro_item: 'CoroItem',
                  is_ordered: bool = True) -> None:
        """ Add item to deferred tasks execution container. """

        if is_ordered:
            await self._ordered_items.put(coro_item)
        else:
            await self._unordered_items.put(coro_item)

    async def _run_unordered(self) -> None:
        unordered = [] #self._unordered_items.copy()
        while not self._unordered_items.empty():
            unordered.append(await self._unordered_items.get())
        try:
            logger.debug(constants.log_unordered_tasks(num=len(unordered)))
            [item.decr() for item in unordered]
            coroutines = [item.build_coro() for item in unordered]
            results = await gather(*coroutines, return_exceptions=True)
        except Exception as e:  # noqa
            # If task will not have time to complete, and some coroutine
            # raises exception this task also raise asyncio.CancelledError
            # TODO: potentially it can create loop when all items wait for only
            #  one that raises exception too fast for some reason. Maybe need
            #  to create additional "chill-container"
            for r, item in zip(results, unordered):  # noqa
                if isinstance(r, Exception) and item.is_active:
                    await self.add(coro_item=item, is_ordered=False)
            logger.debug(
                constants.log_unordered_tasks_complete(
                    num=len(unordered) - len(self._unordered_items)
                )
            )

    async def _run_ordered(self) -> None:
        while not self._ordered_items.empty():
            logger.debug(f'Current tasks num: {self._ordered_items.qsize()}')

            coro_item = await self._ordered_items.get()
            coro = coro_item.build_coro()
            try:
                coro_item.decr()
                logger.debug(f"Execute coro: {coro}")
                resp = await coro
                logger.debug(f"Response: {resp}")
            except HTTPException as e:
                logger.debug(e.detail)
                if coro_item.is_active:
                    await self.add(coro_item)
                continue
            except Exception as e:
                logger.debug(e)
                if coro_item.is_active:
                    await self.add(coro_item)
                continue

    async def start(self, loop: 'AbstractEventLoop') -> None:
        self.event_loop = loop

        while True:
            await self._run_ordered()
            await sleep(self.sleep_seconds)
