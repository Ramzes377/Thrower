from datetime import datetime

from settings import tzMoscow


def default_period(begin: datetime | None = None, end: datetime | None = None):
    return {
        'begin': begin or datetime.utcfromtimestamp(0),
        'end': end or datetime.now(tz=tzMoscow).replace(tzinfo=None)
    }


def query_amount(limit: int = 20):
    return limit
