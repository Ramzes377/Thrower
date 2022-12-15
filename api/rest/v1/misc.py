import datetime
from typing import Hashable, Generator

from httpx import AsyncClient

from api.rest.run import app, base_url


def exist(obj: dict):
    return obj is not None and 'detail' not in obj


async def request(url: str, method: str = 'get', json=None):
    async with AsyncClient(app=app, base_url=base_url) as client:
        handler = getattr(client, method)
        response = await handler(url) if method == 'get' else await handler(url, json=json)
    db_object = response.json()
    return db_object if exist(db_object) else None


def sqllize(dct):
    # replace datetime objects to sql-date strings
    d = {k: v if not isinstance(v, datetime.datetime) else v.strftime('%Y-%m-%dT%H:%M:%S') for k, v in dct.items()}
    d['end'] = d.get('end')  # default end is None
    return d


def desqllize(obj):
    # replace sql-date strings to datetime objects
    iterable = obj.items() if isinstance(obj, dict) else obj
    d = {k: datetime.datetime.strptime(v, '%Y-%m-%dT%H:%M:%S') if k in ['begin', 'end'] else v for k, v in iterable}
    return d


def rm_keys(dct: dict, *keys: Hashable) -> Generator:
    return (dct.pop(key) for key in keys)
