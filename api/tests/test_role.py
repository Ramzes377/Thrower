import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_post_role(client: AsyncClient):
    response = await client.post(
        f"/role",
        json={'id': 20_001, 'app_id': 12_345, 'guild_id': 1}
    )
    data = response.json()
    assert response.status_code == 201
    assert data['id'] == 20_001

    response = await client.post(
        f"/role",
        json={'id': 20_005, 'app_id': 32_534, 'guild_id': 1}
    )
    data = response.json()
    assert response.status_code == 201
    assert data['id'] == 20_005


@pytest.mark.asyncio
async def test_get_role(client: AsyncClient):
    response = await client.get(f"/role/20001")
    data = response.json()
    assert response.status_code == 200
    assert data['id'] == 20_001


@pytest.mark.asyncio
async def test_get_role_emoji(client: AsyncClient):
    response = await client.get(f"/role/20001/emoji")
    data = response.json()
    assert response.status_code == 200
    assert data['id'] == 30_001


@pytest.mark.asyncio
async def test_get_role_info(client):
    response = await client.get(f"/role/20001/info")
    data = response.json()
    assert response.status_code == 200
    assert data['app_name'] == 'AppName'


@pytest.mark.asyncio
async def test_get_all_roles(client: AsyncClient):
    response = await client.get(f"/role")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 2


@pytest.mark.asyncio
async def test_delete_role(client: AsyncClient):
    response = await client.delete(f"/role/20005")
    assert response.status_code == 204
    # trying to delete same role twice
    response = await client.delete(f"/role/20005")
    assert response.status_code == 404  # get 404
