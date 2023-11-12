from contextlib import suppress
from typing import Generator

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from config import Config

Config.local_db_engine = Config.remote_db_engine = 'sqlite+aiosqlite:///'
Config.local_connection = Config.remote_connection = ':memory:'

from api.database import get_session_local  # noqa
from api.base import app  # noqa

TEST_CHANNEL_ID = 1
TEST_USER_ID = 112
ACTIVITY_ID = 12345


@pytest_asyncio.fixture(scope="function")
async def session() -> AsyncSession:
    yield get_session_local()


@pytest_asyncio.fixture(scope="function")
async def client(session: AsyncSession) -> Generator:
    async with AsyncClient(app=app, base_url=Config.base_uri) as client:
        yield client


@pytest_asyncio.fixture()
async def post_users(client: AsyncClient):
    response = await client.post(
        f"/user",
        json={'id': TEST_USER_ID, 'name': 'USER',
              'default_sess_name': 'Session name'}
    )
    assert response.status_code == 201

    response = await client.post(
        f"/user",
        json={'id': TEST_USER_ID + 1, 'name': 'Another USER',
              'default_sess_name': 'Another Session name'}
    )
    assert response.status_code == 201


@pytest_asyncio.fixture()
async def post_activity_info(client: AsyncClient):
    response = await client.post(
        f"/activity_info",
        json={'app_id': 12345, 'app_name': 'AppName', 'icon_url': 'url'}
    )

    return response


@pytest_asyncio.fixture()
async def post_sessions(client: AsyncClient):
    for x in range(1, 6):
        response = await client.post(f"/session",
                                     json={'channel_id': x,
                                           'leader_id': 111 + x - 1,
                                           'creator_id': 111 + x % 2,
                                           'message_id': 321 + 5 * x,
                                           'begin': f'2000-01-01 0{x}:00:00',
                                           'end': f'2000-01-01 0{x + 1}:00:00' if x < 3 else None,
                                           'name': f'{x}' * x}
                                     )
        assert response.status_code == 201


@pytest_asyncio.fixture()
async def post_activity(client: AsyncClient):
    await client.post(
        f"/activity",
        json={'id': ACTIVITY_ID, 'member_id': TEST_USER_ID,
              'begin': '2000-01-01 02:00:00', 'end': None}
    )


@pytest_asyncio.fixture()
async def end_activity(client: AsyncClient):
    await client.patch(
        f"/activity",
        json={'id': ACTIVITY_ID, 'member_id': TEST_USER_ID,
              'end': '2000-01-01 03:45:55'}
    )


@pytest_asyncio.fixture()
async def add_session_member(client: AsyncClient, post_users, post_sessions):
    with suppress(IntegrityError):
        await client.post(
            f"/session/{TEST_CHANNEL_ID}/members/{TEST_USER_ID}"
        )


@pytest_asyncio.fixture()
async def post_role(client: AsyncClient):
    await client.post(
        f"/role",
        json={'id': 20_001, 'app_id': 12_345}
    )
