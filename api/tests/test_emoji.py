import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_post_emoji(client: AsyncClient):
    response = await client.post(
        f"/emoji", json={'id': 30_001, 'role_id': 20_001}
    )
    data = response.json()
    assert response.status_code == 201
    assert data['id'] == 30_001


@pytest.mark.asyncio
async def test_get_role(client: AsyncClient):
    response = await client.get(f"/emoji/30001")
    data = response.json()
    assert response.status_code == 200
    assert data['role_id'] == 20_001
