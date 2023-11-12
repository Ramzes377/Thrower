from functools import partial

from fastapi import Depends
from sqlalchemy.sql.elements import BinaryExpression

from api import tables
from api.specification import AppID, UserID, Unclosed
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

    async def patch(self, activity: EndActivity, *args) -> Activity:
        specification = (AppID(activity.id) & UserID(activity.member_id)
                         & Unclosed())

        current_activity = partial(super().get,
                                   _ordering=self.table.begin.desc())

        return await super().patch(
            specification,
            activity,
            get_method=current_activity,  # noqa
        )
