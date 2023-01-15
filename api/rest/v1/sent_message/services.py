from api.rest.v1 import tables
from api.rest.v1.service import CRUD


class SrvSentMessage(CRUD):
    table = tables.SentMessage
