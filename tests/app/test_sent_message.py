import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def get_all(client: AsyncClient):
    return await client.get(f"/sent_message")


@pytest.mark.asyncio
async def test_post_sent_message(client: AsyncClient):

    response = await client.post(f"/sent_message", json={'id': 1005, 'guild_id': 99999})
    data = response.json()
    assert response.status_code == 201
    assert data['id'] == 1005

    response = await client.post(f"/sent_message", json={'id': 1006, 'guild_id': 99999})
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_get_sent_message(client: AsyncClient):
    response = await client.get(f"/sent_message/1006")
    data = response.json()
    assert response.status_code == 200
    assert data['id'] == 1006

    response = await client.get(f"/sent_message/9876")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_all_sent_messages(client: AsyncClient):
    response = await get_all(client)
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 2


@pytest.mark.asyncio
async def test_delete_sent_message(client: AsyncClient):
    response = await client.delete(f"/sent_message/1006")
    assert response.status_code == 200

    response = await get_all(client)
    data = response.json()
    assert len(data) == 1  # after delete remain only one row
