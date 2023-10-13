from fastapi import Depends
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import BinaryExpression

from api import tables
from api.service import CreateReadUpdate
from api.schemas import IngameSeconds, DurationActivity
from api.specification import Specification
from api.dependencies import default_period

duration = 'sum(COALESCE(CAST(24 * 60 * 60 * (julianday(a."end") - julianday(a.begin)) AS INTEGER),0))'


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
    ) -> list[Session]:
        user = await self.get(user_id)
        filtered = await self._session.scalars(user.sessions.filter(filters))
        return filtered.all()

    async def user_activities(
        self,
        specification: Specification
    ) -> list[DurationActivity]:
        activities = await self._session.scalars(
            select(tables.Activity).filter_by(**specification())
            .filter(tables.Activity.end.isnot(None))
        )
        return activities.all()

    async def durations(self, member_id: Specification) -> list[IngameSeconds]:
        stmt = text(
            f"""
            SELECT a.id app_id, {duration} seconds
                FROM activity a
                    WHERE a.member_id = {member_id._id}
                GROUP BY a.id, a.member_id
            """
        )
        durations = await self._session.execute(stmt)
        return durations.fetchall()

    async def concrete_duration(
        self,
        member_id: Specification,
        role_id: Specification
    ) -> IngameSeconds | None:

        stmt = text(
            f"""
            SELECT a.id app_id, {duration} seconds
            FROM activity a
                JOIN role r ON r.id = {role_id._id} and r.app_id = a.id
                WHERE a.member_id = {member_id._id}
            GROUP BY a.id, a.member_id
        """)

        concrete_duration = await self._session.execute(stmt)
        return concrete_duration.fetchone()
