from datetime import datetime

from api.rest.v1 import tables
from api.rest.v1.misc import rm_keys, desqllize
from api.rest.v1.schemas import Activity, Role, ActivityInfo, Emoji

from api.rest.v1.base_service import BaseService


class SrvActivities(BaseService):
    def get_all(self, begin: datetime, end: datetime) -> list[Activity]:
        return (
            self._session.query(tables.Activity)
                .filter(tables.Activity.begin.between(begin, end))
                .all()
        )

    def get(self, app_id: int) -> Activity:
        return (
            self._session.query(tables.Activity)
                .filter_by(id=app_id)
                .first()
        )

    def post(self, activitydata: Activity) -> tables.Activity:
        activity = tables.Activity(**activitydata.dict())
        self._db_add_obj(activity)
        return activity

    def put(self, activityedit: Activity | dict) -> Activity:
        app_id, member_id = rm_keys(activityedit, 'id', 'member_id')
        activityedit = desqllize(activityedit)
        activity = (
            self._session.query(tables.Activity)
                .filter_by(id=app_id, member_id=member_id, end=None)
                .order_by(tables.Activity.begin.desc())
                .first()
        )
        self._db_edit_obj(activity, activityedit)
        return activity

    def get_info(self, app_id: int) -> ActivityInfo:
        return self.get(app_id).info

    def _role(self, app_id: int):
        return (
            self._session.query(tables.Role)
                .join(tables.Activity)
                .filter_by(id=app_id)
        )

    def get_role(self, app_id: int) -> Role:
        return self._role(app_id).first()

    def get_emoji(self, app_id: int) -> Emoji:
        return (
            self._session.query(tables.Emoji)
                .join(self._role(app_id))
                .first()
        )
