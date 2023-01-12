import datetime
from typing import Hashable, Generator

import aiohttp


async def request(url: str, data: dict = None, method: str = 'get'):
    # example deprecated
    # await request('/session/', data, method='post')
    async with aiohttp.ClientSession('base_url') as session:
        _method = getattr(session, method)
        async with _method(url, json=data) as resp:
            response = await resp.json()
    return response


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


def rm_keys(dct: dict, *keys: str) -> Generator:
    return (dct.pop(key) for key in keys)
