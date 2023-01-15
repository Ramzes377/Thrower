from api.rest.v1 import tables
from api.rest.v1.service import Read


class SrvActivityInfo(Read):
    table = tables.ActivityInfo
