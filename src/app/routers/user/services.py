from fastapi import Depends
from sqlalchemy import select, text, Sequence
from sqlalchemy.sql.elements import BinaryExpression

from src.app import tables
from src.constants import constants
from src.app.service import CreateReadUpdate
from src.app.schemas import IngameSeconds
from src.app.specification import Specification
from src.app.dependencies import default_period


class SrvUser(CreateReadUpdate):
    table = tables.Member

    @classmethod
    def filter_by_timeperiod(
            cls,
            period: dict = Depends(default_period)
    ) -> BinaryExpression:
        return tables.Session.begin.between(period['begin'], period['end'])

    async def get_sessions(
            self,
            user_id: Specification,
            filters: BinaryExpression = None
    ) -> Sequence:
        user = await self.get(user_id)

        async with self._session.begin():
            filtered = await self._session.execute(
                user.sessions.filter(filters))
            filtered = filtered.scalars().all()

        return filtered

    async def user_activities(
            self,
            specification: Specification
    ) -> Sequence:
        activities = await self._session.scalars(
            select(tables.Activity).filter_by(**specification())
            .filter(tables.Activity.end.isnot(None))
        )

        return activities.all()

    async def durations(self, member_id: Specification) -> Sequence:
        stmt = text(constants.duration_query(member_id=member_id.value))
        durations = await self._session.execute(stmt)
        return durations.fetchall()

    async def concrete_duration(
            self,
            member_id: Specification,
            role_id: Specification
    ) -> IngameSeconds | None:
        stmt = text(constants.concrete_duration_query(role_id=role_id.value,
                                                      member_id=member_id.value))
        concrete_duration = await self._session.execute(stmt)
        return concrete_duration.fetchone()
