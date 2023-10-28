from typing import Generator

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession, create_async_engine, async_sessionmaker,
)

from config import Config
from api.base import app
from api.tables import session_fabric

TEST_CHANNEL_ID = 1
TEST_USER_ID = 112
ACTIVITY_ID = 12345

engine = create_async_engine(
    Config.DB_ENGINE + ':memory:',
    echo=False,
    connect_args={"check_same_thread": False}
)
async_session = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

get_session = session_fabric(async_session, engine)


@pytest_asyncio.fixture(scope="function")
async def session() -> AsyncSession:
    yield async_session()


@pytest_asyncio.fixture(scope="function")
async def client(session: AsyncSession) -> Generator:
    async with AsyncClient(app=app, base_url=Config.BASE_URI) as client:
        yield client


@pytest_asyncio.fixture()
async def post_user(client: AsyncClient):
    try:
        response = await client.post(
            f"/user",
            json={'id': TEST_USER_ID, 'name': 'USER',
                  'default_sess_name': 'Session name'}
        )
        assert response.status_code == 201
    except:
        pass


@pytest_asyncio.fixture()
async def post_activity_info(client: AsyncClient):
    try:
        response = await client.post(
            f"/activity_info",
            json={'app_id': 12345, 'app_name': 'AppName', 'icon_url': 'url'}
        )
    except:
        response = await client.get(f"/activity_info/12345")
    return response


@pytest_asyncio.fixture()
async def post_sessions(client: AsyncClient):
    for x in range(1, 6):
        try:
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
        except:
            return


@pytest_asyncio.fixture()
async def post_activity(client: AsyncClient):
    try:
        await client.post(
            f"/activity",
            json={'id': ACTIVITY_ID, 'member_id': TEST_USER_ID,
                  'begin': '2000-01-01 02:00:00', 'end': None}
        )
    except Exception as e:
        pass


@pytest_asyncio.fixture()
async def end_activity(client: AsyncClient):
    try:
        await client.patch(
            f"/activity",
            json={'id': ACTIVITY_ID, 'member_id': TEST_USER_ID,
                  'end': '2000-01-01 03:45:55'}
        )
    except:
        pass


@pytest_asyncio.fixture()
async def add_session_member(client: AsyncClient, post_user, post_sessions):
    try:
        await client.post(
            f"/session/{TEST_CHANNEL_ID}/members/{TEST_USER_ID}"
        )
    except:
        pass


@pytest_asyncio.fixture()
async def post_role(client: AsyncClient):
    try:
        await client.post(
            f"/role",
            json={'id': 20_001, 'app_id': 12_345}
        )
    except:
        pass