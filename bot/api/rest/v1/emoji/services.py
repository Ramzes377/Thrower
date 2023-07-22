try:
    from api.rest.v1 import tables
    from api.rest.v1.service import CreateRead
except ModuleNotFoundError:
    from bot.api.rest.v1 import tables
    from bot.api.rest.v1.service import CreateRead

class SrvEmoji(CreateRead):
    table = tables.Emoji
