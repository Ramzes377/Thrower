import pytest
from httpx import AsyncClient

activity_id = 12345


@pytest.mark.asyncio
async def test_post_activity_info(post_activity_info):
    response = post_activity_info
    data = response.json()
    assert response.status_code in (200, 201)
    assert data['app_name'] == 'AppName'


@pytest.mark.asyncio
async def test_get_activity_info(client: AsyncClient, post_activity_info):
    response = await client.get(f"/activity_info/{activity_id}")
    data = response.json()
    assert response.status_code == 200
    assert data['app_name'] == 'AppName'


@pytest.mark.asyncio
async def test_get_all_activity_info(client: AsyncClient):
    response = await client.get(f"/activity_info")
    data = response.json()
    assert response.status_code == 200
    assert isinstance(data, list) and len(data) == 1
