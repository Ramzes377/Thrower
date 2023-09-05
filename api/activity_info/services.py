from api import tables
from api.service import CreateRead


class SrvActivityInfo(CreateRead):
    table = tables.ActivityInfo
