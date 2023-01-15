from datetime import datetime

from settings import tzMoscow


def default_period(begin: datetime | None = None, end: datetime | None = None):

    return {'begin': begin or datetime.fromordinal(1), 'end': end or datetime.now(tz=tzMoscow)}


def query_amount(limit: int = 20):
    return limit
