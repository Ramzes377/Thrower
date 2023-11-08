import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_post_music(client: AsyncClient, post_user):
    response = await client.post(
        f"/favorite_music",
        json={'user_id': 122, 'query': 'http://some-url.com',
              'title': 'Track Name'}
    )
    data = response.json()
    assert response.status_code == 201
    assert data['counter'] == 1  # create user-music note

    response = await client.post(
        f"/favorite_music",
        json={'user_id': 122, 'query': 'http://some-url.com'}
    )
    data = response.json()
    assert response.status_code == 201
    assert data['counter'] == 2  # update user-music note

    response = await client.post(
        f"/favorite_music",
        json={'user_id': 122, 'query': 'http://some-another-url.com'}
    )
    assert response.status_code == 201  # create another user-music note


@pytest.mark.asyncio
async def test_get_music(client: AsyncClient):
    response = await client.get(f"/favorite_music/122")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 2
