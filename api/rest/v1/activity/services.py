from fastapi import Depends
from sqlalchemy.sql.elements import BinaryExpression

from .. import tables
from ..base_specification import Specification
from ..dependencies import default_period
from ..specifications import AppID, UserID, Unclosed
from ..schemas import Activity, EndActivity
from ..service import CreateReadUpdate


class SrvActivities(CreateReadUpdate):
    table = tables.Activity
    order_by = tables.Activity.begin

    @classmethod
    def filter_by_timeperiod(cls, period: dict = Depends(default_period)) -> BinaryExpression:
        return cls.table.begin.between(period['begin'], period['end'])

    def _current_activity(self, specification: Specification):
        return (
            self._base_query
            .filter_by(**specification())
            .order_by(self.table.begin.desc())
            .first()
        )

    def patch(self, activity: EndActivity, *args) -> Activity:
        specification = AppID(activity.id) & UserID(activity.member_id) & Unclosed()
        return super().patch(specification, activity, get_method=self._current_activity)

