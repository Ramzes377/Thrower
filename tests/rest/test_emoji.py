from fastapi.testclient import TestClient
from api.rest.base import base_url
from tests.rest._client import client_fixture, session_fixture


def test_post_emoji(client: TestClient):
    response = client.post(f"{base_url}/emoji/", json={'id': 30_001, 'role_id': 20_001})
    data = response.json()
    assert response.status_code == 201
    assert data['id'] == 30_001


def test_get_role(client: TestClient):
    response = client.get(f"{base_url}/emoji/30001")
    data = response.json()
    assert response.status_code == 200
    assert data['role_id'] == 20_001
