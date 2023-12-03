import datetime

import pytest
from httpx import AsyncClient

from src.app.dependencies import default_period

TEST_CHANNEL_ID = 1
TEST_USER_ID = 112
TEST_MSG_ID = 326


@pytest.mark.asyncio
async def test_post_sessions(client: AsyncClient, post_sessions):
    response = await client.post(f"/session",
                                 json={'channel_id': 'Invalid data'}
                                 )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_all_sessions(client: AsyncClient):
    response = await client.get(f"/session")
    data_without_params = response.json()

    response = await client.get(f"/session", params=default_period())
    data_with_default_params = response.json()

    assert (isinstance(data_without_params, list)
            and data_without_params == data_with_default_params)

    response = await client.get(
        f"/session",
        params=default_period(begin=datetime.datetime(2000, 1, 1, 3))
    )
    data_with_params = response.json()
    assert len(data_with_params) == 3


@pytest.mark.asyncio
async def test_unclosed_sessions(client: AsyncClient):
    response = await client.get(f"/session/unclosed")
    unclosed_sessions = response.json()  # last 3 channels
    assert len(unclosed_sessions) == 3


@pytest.mark.asyncio
async def test_get_session(client: AsyncClient):
    response = await client.get(f"/session/{TEST_CHANNEL_ID}")
    data = response.json()

    assert response.status_code == 200
    assert data['channel_id'] == TEST_CHANNEL_ID
    assert data["name"] == "1"
    assert data["begin"] is not None

    response = await client.get(f"/session/by_msg/{data['message_id']}")
    data = response.json()

    assert response.status_code == 200
    assert data['channel_id'] == TEST_CHANNEL_ID
    assert data["name"] == "1"
    assert data["begin"] is not None


@pytest.mark.asyncio
async def test_patch_session(client: AsyncClient):
    new_name = 'Modified'
    response = await client.patch(
        f"/session/{TEST_CHANNEL_ID}",
        json={'name': new_name}
    )
    data = response.json()
    assert data['name'] == new_name
    response = await client.patch(
        f"/session/{TEST_CHANNEL_ID}",
        json={'name': '1'}
    )
    data = response.json()
    assert data['name'] == '1'


@pytest.mark.asyncio
async def test_add_session_member(client: AsyncClient, post_users):
    response = await client.post(
        f"/session/{TEST_CHANNEL_ID}/members/{TEST_USER_ID}"
    )
    data = response.json()

    assert response.status_code == 201
    assert isinstance(data['id'], int)

    response = await client.post(
        f"/session/{TEST_CHANNEL_ID}/members/{TEST_USER_ID}"
    )
    same_data = response.json()
    assert data == same_data


@pytest.mark.asyncio
async def test_get_session_members(client: AsyncClient):
    response = await client.get(f"/session/{TEST_CHANNEL_ID}/members")
    data = response.json()

    assert response.status_code == 200
    assert isinstance(data, list) and len(data) == 1


@pytest.mark.asyncio
async def test_get_session_leadership(client: AsyncClient):
    response = await client.get(f"/session/{TEST_MSG_ID}/leadership")
    data = response.json()
    assert response.status_code == 200
    assert isinstance(data, list) and len(data) == 2


@pytest.mark.asyncio
async def test_get_session_presence(client: AsyncClient):
    response = await client.get(f"/session/{TEST_MSG_ID}/prescence")
    data = response.json()
    assert response.status_code == 200
    assert isinstance(data, list) and len(data) == 2


@pytest.mark.asyncio
async def test_get_session_activities(client: AsyncClient):
    response = await client.get(f"/session/{TEST_MSG_ID}/activities")
    data = response.json()
    assert response.status_code == 200
    assert isinstance(data, list) and len(data) == 1
