import pytest
from fastapi.testclient import TestClient

from api.rest.base import base_url


@pytest.fixture
def post_activityinfo(client: TestClient):
    try:
        response = client.post(f"{base_url}/activityinfo/", json={'app_id': 12345, 'app_name': 'AppName',
                                                                  'icon_url': 'url'})
    except:
        response = client.get(f"{base_url}/activityinfo/12345")
    return response


def test_post_activityinfo(post_activityinfo):
    response = post_activityinfo
    data = response.json()
    assert response.status_code in (200, 201)
    assert data['app_name'] == 'AppName'


def test_get_activityinfo(client: TestClient):
    response = client.get(f"{base_url}/activityinfo/12345")
    data = response.json()
    assert response.status_code == 200
    assert data['app_name'] == 'AppName'


def test_get_all_activityinfo(client: TestClient):
    response = client.get(f"{base_url}/activityinfo/")
    data = response.json()
    assert response.status_code == 200
    assert isinstance(data, list) and len(data) == 1
