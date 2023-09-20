from fastapi import HTTPException, status, Depends
from sqlalchemy import select
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

    async def unclosed(self) -> list[Session]:
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
        executed = await self._session.scalars(
            select(tables.Member).filter_by(**user_specification())
        )
        user = executed.first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        session: tables.Session = await self.get(sess_specification)
        session.members.append(user)
        await self.create(session)
        return user
