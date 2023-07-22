from datetime import datetime

try:
    from utils import now
except ModuleNotFoundError:
    from bot.utils import now


def default_period(begin: datetime | None = None, end: datetime | None = None):
    return {
        'begin': begin or datetime.utcfromtimestamp(0),
        'end': end or now()
    }


def limit(amount: int = 20):
    return amount
