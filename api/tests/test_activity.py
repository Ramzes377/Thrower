import pytest
from httpx import AsyncClient

activity_id = 12345
member_id = 112


@pytest.mark.asyncio
async def test_post_activity(client: AsyncClient, post_activity):
    pass


@pytest.mark.asyncio
async def test_patch_activity(client: AsyncClient):
    response = await client.patch(
        f"/activity",
        json={'id': activity_id, 'member_id': member_id,
              'end': '2000-01-01 03:45:55'}
    )
    data = response.json()
    assert response.status_code == 200
    assert data['end'] is not None


@pytest.mark.asyncio
async def test_get_activity(client: AsyncClient):
    response = await client.get(f"/activity/{activity_id}")
    data = response.json()
    assert response.status_code == 200
    assert data['end'] is not None


@pytest.mark.asyncio
async def test_get_activity_info(client, post_activity_info):
    response = await client.get(f"/activity/{activity_id}/info")
    data = response.json()
    assert response.status_code == 200
    assert isinstance(data, dict)
