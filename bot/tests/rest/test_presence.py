from fastapi.testclient import TestClient

from bot.api.rest.base import base_url


def test_post_presences(client: TestClient, post_sessions):
    response = client.post(f"{base_url}/prescence/", json={'channel_id': 1, 'member_id': 112,
                                                           'begin': '2000-01-01 02:00:00'})
    data = response.json()
    assert response.status_code == 201
    assert data['end'] is None


def test_patch_presences(client: TestClient):
    response = client.patch(f"{base_url}/prescence/", json={'channel_id': 1, 'member_id': 112,
                                                            'end': '2000-01-01 03:30:00'})
    data = response.json()

    assert response.status_code == 200
    assert data['end'] is not None

    response = client.patch(f"{base_url}/prescence/", json={'channel_id': 2, 'member_id': 'Invalid data'})
    assert response.status_code == 422


def test_get_presences(client: TestClient):
    response = client.get(f"{base_url}/prescence/1")
    data = response.json()
    assert response.status_code == 200
    assert isinstance(data, list) and len(data) == 1


def test_get_by_msg_presences(client: TestClient):
    response = client.get(f"{base_url}/prescence/by_msg/326")
    data = response.json()
    assert response.status_code == 200
    assert isinstance(data, list) and len(data) == 1
