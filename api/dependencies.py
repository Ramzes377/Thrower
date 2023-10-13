from datetime import datetime

from utils import now


def default_period(begin: datetime | None = None, end: datetime | None = None):
    return {
        'begin': begin or datetime.utcfromtimestamp(0),
        'end': end or now()
    }


def limit(amount: int = 20) -> int:
    return amount


def params_guild_id(guild_id: int = 0) -> int:
    return guild_id
