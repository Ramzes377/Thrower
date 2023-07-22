from fastapi.testclient import TestClient

from bot.api.rest.base import base_url


def get_all(client: TestClient):
    return client.get(f"{base_url}/sent_message/")


def test_post_sent_message(client: TestClient):
    response = client.post(f"{base_url}/sent_message/", json={'id': 1005})
    data = response.json()
    assert response.status_code == 201
    assert data['id'] == 1005

    response = client.post(f"{base_url}/sent_message/", json={'id': 1006})
    assert response.status_code == 201


def test_get_sent_message(client: TestClient):
    response = client.get(f"{base_url}/sent_message/1006")
    data = response.json()
    assert response.status_code == 200
    assert data['id'] == 1006

    response = client.get(f"{base_url}/sent_message/9876")
    assert response.status_code == 404


def test_get_all_sent_messages(client: TestClient):
    response = get_all(client)
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 2


def test_delete_sent_message(client: TestClient):
    response = client.delete(f"{base_url}/sent_message/1006")
    assert response.status_code == 200

    response = get_all(client)
    data = response.json()
    assert len(data) == 1  # after delete remain only one row
