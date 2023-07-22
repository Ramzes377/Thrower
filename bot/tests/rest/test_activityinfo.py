from fastapi.testclient import TestClient

from bot.api.rest.base import base_url

activity_id = 12345


def test_post_activityinfo(post_activityinfo):
    response = post_activityinfo
    data = response.json()
    assert response.status_code in (200, 201)
    assert data['app_name'] == 'AppName'


def test_get_activityinfo(client: TestClient):
    response = client.get(f"{base_url}/activityinfo/{activity_id}")
    data = response.json()
    assert response.status_code == 200
    assert data['app_name'] == 'AppName'


def test_get_all_activityinfo(client: TestClient):
    response = client.get(f"{base_url}/activityinfo/")
    data = response.json()
    assert response.status_code == 200
    assert isinstance(data, list) and len(data) == 1
