from api.rest.v1 import tables
from api.rest.v1.schemas import ActivityInfo

from api.rest.v1.base_service import BaseService


class SrvActivityInfo(BaseService):

    def get(self, app_id: int) -> ActivityInfo:
        return (
            self._session.query(tables.ActivityInfo)
            .filter_by(app_id=app_id)
            .first()
        )

    def get_all(self) -> list[ActivityInfo]:
        return self._session.query(tables.ActivityInfo).all()
