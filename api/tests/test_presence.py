import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_post_presences(client: AsyncClient, post_sessions):
    response = await client.post(f"/prescence",
                                 json={'channel_id': 1, 'member_id': 112,
                                       'begin': '2000-01-01 02:00:00'}
                                 )
    data = response.json()
    assert response.status_code == 201
    assert data['end'] is None


@pytest.mark.asyncio
async def test_patch_presences(client: AsyncClient):
    response = await client.patch(
        f"/prescence",
        json={'channel_id': 1, 'member_id': 112, 'end': '2000-01-01 03:30:00'}
    )
    data = response.json()

    assert response.status_code == 200
    assert data['end'] is not None

    response = await client.patch(
        f"/prescence",
        json={'channel_id': 2, 'member_id': 'Invalid data'}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_presences(client: AsyncClient):
    response = await client.get(f"/prescence/1")
    data = response.json()
    assert response.status_code == 200
    assert isinstance(data, list) and len(data) == 1


@pytest.mark.asyncio
async def test_get_by_msg_presences(client: AsyncClient):
    response = await client.get(f"/prescence/by_msg/326")
    data = response.json()
    assert response.status_code == 200
    assert isinstance(data, list) and len(data) == 1
