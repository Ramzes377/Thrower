from fastapi.testclient import TestClient

from bot.api.rest.base import base_url


def test_post_role(client: TestClient):
    response = client.post(f"{base_url}/role/", json={'id': 20_001, 'app_id': 12_345})
    data = response.json()
    assert response.status_code == 201
    assert data['id'] == 20_001

    response = client.post(f"{base_url}/role/", json={'id': 20_005, 'app_id': 32_534})
    data = response.json()
    assert response.status_code == 201
    assert data['id'] == 20_005


def test_get_role(client: TestClient):
    response = client.get(f"{base_url}/role/20001")
    data = response.json()
    assert response.status_code == 200
    assert data['id'] == 20_001


def test_get_role_emoji(client: TestClient):
    response = client.get(f"{base_url}/role/20001/emoji")
    data = response.json()
    assert response.status_code == 200
    assert data['id'] == 30_001


def test_get_role_info(client: TestClient, post_activityinfo):
    response = client.get(f"{base_url}/role/20001/info")
    data = response.json()
    assert response.status_code == 200
    assert data['app_name'] == 'AppName'


def test_get_all_roles(client: TestClient):
    response = client.get(f"{base_url}/role/")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 2


def test_delete_role(client: TestClient):
    response = client.delete(f"{base_url}/role/20005")
    assert response.status_code == 204

    response = client.delete(f"{base_url}/role/20005")  # trying to delete same role twice
    assert response.status_code == 404  # get 404
