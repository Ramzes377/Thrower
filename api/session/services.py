from fastapi import Depends
from sqlalchemy import select, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Query
from sqlalchemy.sql.elements import BinaryExpression

from api import tables
from api.specification import Specification
from api.dependencies import default_period
from api.schemas import Session
from api.service import CreateReadUpdate
from api.specification import Unclosed


class SrvSession(CreateReadUpdate):
    table = tables.Session
    order_by = tables.Session.begin

    @classmethod
    def filter_by_timeperiod(
            cls,
            period: dict = Depends(default_period)
    ) -> BinaryExpression:
        return cls.table.begin.between(period['begin'], period['end'])

    def _unclosed(self) -> Query:
        unclosed_specification = Unclosed()
        return (
            self._base_query
            .filter_by(**unclosed_specification())
            .order_by(tables.Session.begin.desc())
        )

    async def unclosed(self) -> Sequence:
        unclosed = await self._session.scalars(self._unclosed())
        return unclosed.all()

    async def user_unclosed(self, leader_id: Specification) -> Session | None:
        user_unclosed = await self._session.scalars(
            self._unclosed()
            .filter_by(**leader_id())
        )
        return user_unclosed.first()

    async def add_member(
            self,
            sess_specification: Specification,
            user_specification: Specification
    ) -> tables.Member:
        async def _add_member(session: AsyncSession) -> tables.Member:
            query = select(tables.Member).filter_by(**user_specification())

            user = await self.get(_query=query, session_=session)
            session_table: tables.Session = await self.get(sess_specification,
                                                           session_=session)
            session_table.members.append(user)

            await self._create(object_=session_table, session=session)
            return user

        return await self.reflect_execute(_add_member)
