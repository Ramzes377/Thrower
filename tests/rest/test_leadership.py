from fastapi.testclient import TestClient

from api.rest.base import base_url
from _client import client_fixture, session_fixture


def test_post_leadership(client: TestClient):
    response = client.post(f"{base_url}/leadership/", json={'channel_id': 1, 'member_id': 112,
                                                            'begin': '2000-01-01 02:00:00'})
    # initiate leadership  of channel
    data = response.json()
    assert response.status_code == 201
    assert data['begin'] == '2000-01-01 02:00:00'
    assert data['end'] is None

    response = client.post(f"{base_url}/leadership/", json={'channel_id': 1, 'member_id': 113,
                                                            'begin': '2000-01-01 03:00:00'})
    # add new leader, end leadership of previous leader
    data = response.json()
    assert response.status_code == 202
    assert data['begin'] == '2000-01-01T03:00:00'
    assert data['member_id'] == 113
    assert data['end'] is None

    response = client.post(f"{base_url}/leadership/", json={'channel_id': 1, 'member_id': None,
                                                            'begin': '2000-01-01 04:00:00'})
    # mark leader as finishing
    data = response.json()
    assert response.status_code == 202
    assert data['member_id'] == 113
    assert data['begin'] == '2000-01-01T03:00:00'
    assert data['end'] == '2000-01-01T04:00:00'  # end leadership of session


def test_get_leadership(client: TestClient):
    response = client.get(f"{base_url}/leadership/1")
    data = response.json()
    assert response.status_code == 200
    assert data['end'] == '2000-01-01 04:00:00'


def test_get_leadership_history(client: TestClient):
    response = client.get(f"{base_url}/leadership/hist/1")
    data = response.json()
    assert response.status_code == 200
    assert isinstance(data, list) and len(data) == 2
