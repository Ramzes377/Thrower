from functools import partial
from typing import Annotated, Callable, TYPE_CHECKING, Optional

from fastapi import Depends, Query

from sqlalchemy.ext.asyncio import AsyncSession

from src.app import tables
from src.app.schemas import SessionLike, AnyFields
from src.app.service import CreateReadUpdate
from src.app.specification import SessionID, UserID, Unclosed
from src.app.dependencies import db_sessions

if TYPE_CHECKING:
    from sqlalchemy import Sequence, Select, BinaryExpression
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.app.specification import Specification


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

        self._default_query = self._base_query
        self._base_query = self._base_query.join(tables.Session)

    async def all(
            self,
            filter_: Optional['BinaryExpression'] = None,
            specification: Optional['Specification'] = None,
            *,
            query: Optional['Select'] = None,
            join_sessions: bool = True,
            **kwargs,

    ) -> 'Sequence':
        query = self._base_query if join_sessions else self._default_query
        return await super().all(specification=specification, query=query)

    async def patch(
            self,
            prescence: SessionLike,
            *args,
            get_method: Callable = None,
            session_: AsyncSession = None,
            **kwargs
    ) -> SessionLike:
        specification = (SessionID(prescence.channel_id) &
                         UserID(prescence.member_id) & Unclosed())

        query = (
            self._default_query
            .filter_by(**specification())
            .order_by(tables.Prescence.begin.desc())
        )
        member_prescence = partial(super().get, _query=query)

        return await super().patch(
            specification=specification,
            data=AnyFields(end=prescence.end),
            get_method=member_prescence,  # noqa
        )
