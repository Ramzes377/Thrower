from api import tables
from api.service import CRUD


class SrvSentMessage(CRUD):
    table = tables.SentMessage
