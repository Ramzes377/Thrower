from fastapi.testclient import TestClient

from api.rest.base import base_url


activity_id = 12345
member_id = 112


def test_post_activity(client: TestClient):
    response = client.post(f"{base_url}/activity/", json={'id': activity_id, 'member_id': member_id,
                                                          'begin': '2000-01-01 02:00:00'})
    data = response.json()
    assert response.status_code == 201
    assert data['end'] is None


def test_patch_activity(client: TestClient):
    response = client.patch(f"{base_url}/activity/", json={'id': activity_id, 'member_id': member_id,
                                                           'end': '2000-01-01 03:45:55'})
    data = response.json()
    assert response.status_code == 200
    assert data['end'] is not None


def test_get_activity(client: TestClient):
    response = client.get(f"{base_url}/activity/{activity_id}")
    data = response.json()
    assert response.status_code == 200
    assert data['end'] is not None


def test_get_activity_info(client: TestClient, post_activityinfo):
    response = client.get(f"{base_url}/activity/{activity_id}/info")
    data = response.json()
    assert response.status_code == 200
    assert isinstance(data, dict)
