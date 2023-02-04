from fastapi.testclient import TestClient

from api.rest.base import base_url
from _client import client_fixture, session_fixture
from test_activityinfo import post_activityinfo


def test_post_activity(client: TestClient):
    response = client.post(f"{base_url}/activity/", json={'id': 12345, 'member_id': 112,
                                                          'begin': '2000-01-01 02:00:00'})
    data = response.json()
    assert response.status_code == 201
    assert data['end'] is None


def test_patch_activity(client: TestClient):
    response = client.patch(f"{base_url}/activity/", json={'id': 12345, 'member_id': 112,
                                                           'end': '2000-01-01 03:45:55'})
    data = response.json()
    assert response.status_code == 200
    assert data['end'] is not None


def test_get_activity(client: TestClient):
    response = client.get(f"{base_url}/activity/12345")  # get activity with id 12345
    data = response.json()
    assert response.status_code == 200
    assert data['end'] is not None


def test_get_activity_info(client: TestClient, post_activityinfo):
    response = client.get(f"{base_url}/activity/12345/info")
    data = response.json()
    assert response.status_code == 200
    assert isinstance(data, dict)


