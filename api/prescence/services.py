from functools import partial
from typing import Annotated, Callable

from fastapi import Depends, Query
from sqlalchemy import Sequence, BinaryExpression, Select
from sqlalchemy.ext.asyncio import AsyncSession

from api import tables
from api.specification import Specification
from api.schemas import Prescence, EndPrescence
from api.service import CreateReadUpdate
from api.specification import SessionID, UserID, Unclosed
from api.dependencies import db_sessions


class SrvPrescence(CreateReadUpdate):
    table = tables.Prescence
    order_by = table.begin

    def __init__(
            self,
            sessions: tuple[AsyncSession, ...] = Depends(db_sessions),
            defer_handle: Annotated[
                bool, Query(include_in_schema=False)
            ] = True,
    ):
        super().__init__(sessions, defer_handle)
        # override base query to use base method _get
        # more native way with filter by message_id
        self._default_query = self._base_query
        self._base_query = self._base_query.join(tables.Session)

    async def all(
            self,
            filter_: BinaryExpression | None = None,
            specification: Specification | None = None,
            *,
            query: Select | None = None,
            join_sessions: bool = True,
            **kwargs,

    ) -> Sequence:
        query = self._base_query if join_sessions else self._default_query
        return await super().all(specification=specification, query=query)

    async def patch(
            self,
            prescence: EndPrescence,
            *args,
            get_method: Callable = None,
            session_: AsyncSession = None,
            **kwargs
    ) -> Prescence:
        specification = (
                SessionID(prescence.channel_id) &
                UserID(prescence.member_id) & Unclosed()
        )

        query = self._default_query.order_by(tables.Prescence.begin.desc())
        member_prescence = partial(super().get, _query=query,
                                   _multiple_result=True)

        return await super().patch(
            specification=specification,
            data={'end': prescence.end},
            get_method=member_prescence,  # noqa
            _multiple_result=True
        )
