import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_post_leadership(client: AsyncClient):
    response = await client.post(f"/leadership",
                                 json={'channel_id': 1, 'member_id': 112,
                                       'begin': '2000-01-01 02:00:00'}
                                 )
    # initiate leadership  of channel
    data = response.json()
    assert response.status_code == 201
    assert data['begin'] == '2000-01-01 02:00:00'
    assert data['end'] is None

    response = await client.post(f"/leadership",
                                 json={'channel_id': 1, 'member_id': 113,
                                       'begin': '2000-01-01 03:00:00'}
                                 )
    # add new leader, end leadership of previous leader
    data = response.json()
    assert response.status_code == 202
    assert data['begin'] == '2000-01-01T03:00:00'
    assert data['member_id'] == 113
    assert data['end'] is None

    response = await client.post(f"/leadership",
                                 json={'channel_id': 1, 'member_id': None,
                                       'begin': '2000-01-01 04:00:00'}
                                 )
    # mark leader as finishing
    data = response.json()
    assert response.status_code == 202
    assert data['member_id'] == 113
    assert data['begin'] == '2000-01-01T03:00:00'
    assert data['end'] == '2000-01-01T04:00:00'  # end leadership of session


@pytest.mark.asyncio
async def test_get_leadership(client: AsyncClient):
    response = await client.get(f"/leadership/1")
    data = response.json()
    assert response.status_code == 200
    assert data['end'] == '2000-01-01 04:00:00'


@pytest.mark.asyncio
async def test_get_leadership_history(client: AsyncClient):
    response = await client.get(f"/leadership/hist/1")
    data = response.json()
    assert response.status_code == 200
    assert isinstance(data, list) and len(data) == 2
