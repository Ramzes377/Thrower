from api.rest.v1 import tables
from api.rest.v1.service import CreateRead


class SrvActivityInfo(CreateRead):
    table = tables.ActivityInfo
