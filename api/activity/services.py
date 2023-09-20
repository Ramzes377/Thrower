from fastapi import Depends
from sqlalchemy.sql.elements import BinaryExpression

from api import tables
from api.specification import Specification, AppID, UserID, Unclosed
from api.dependencies import default_period
from api.schemas import Activity, EndActivity
from api.service import CreateReadUpdate


class SrvActivities(CreateReadUpdate):
    table = tables.Activity
    order_by = tables.Activity.begin

    @classmethod
    def filter_by_timeperiod(
        cls,
        period: dict = Depends(default_period)
    ) -> BinaryExpression:
        return cls.table.begin.between(period['begin'], period['end'])

    async def _current_activity(self, specification: Specification):
        current_activity = await self._session.scalars(
            self._base_query
            .filter_by(**specification())
            .order_by(self.table.begin.desc())
        )
        return current_activity.first()

    async def patch(self, activity: EndActivity, *args) -> Activity:
        specification = (AppID(activity.id) & UserID(activity.member_id)
                         & Unclosed())
        return await super().patch(
            specification,
            activity,
            get_method=self._current_activity
        )
