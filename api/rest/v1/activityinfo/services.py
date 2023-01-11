from api.rest.v1 import tables
from api.rest.v1.schemas import ActivityInfo

from api.rest.v1.service import Read


class SrvActivityInfo(Read):
    table = tables.ActivityInfo

    def all(self) -> list[ActivityInfo]:
        return super().all().all()
