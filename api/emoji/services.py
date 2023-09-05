from api import tables
from api.service import CreateRead


class SrvEmoji(CreateRead):
    table = tables.Emoji
