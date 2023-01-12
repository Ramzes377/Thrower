from datetime import datetime

from .. import tables
from ..specifications import AppID, UserID, Unclosed
from ..misc import rm_keys, desqllize
from ..schemas import Activity
from ..service import CreateReadUpdate


class SrvActivities(CreateReadUpdate):
    table = tables.Activity

    def all(self, begin: datetime, end: datetime) -> list[Activity]:
        return super().all().filter(tables.Activity.begin.between(begin, end)).all()

    def patch(self, activity_data: Activity | dict, *args) -> Activity:
        if isinstance(activity_data, Activity):
            activity_data = activity_data.dict()

        app_id, member_id = rm_keys(activity_data, 'id', 'member_id')
        activity_data = desqllize(activity_data)
        specification = AppID(app_id) & UserID(member_id) & Unclosed(None)
        activity = self._base_query.filter_by(**specification()).order_by(self.table.begin.desc()).first()
        self.update(activity, activity_data)
        return activity
