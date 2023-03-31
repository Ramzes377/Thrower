from fastapi.testclient import TestClient

from api.rest.base import base_url


def test_post_music(client: TestClient, post_user):
    response = client.post(f"{base_url}/favoritemusic/", json={'user_id': 122, 'query': 'http://some-url.com',
                                                               'title': 'Track Name'})
    data = response.json()
    assert response.status_code == 201
    assert data['counter'] == 1  # create user-music note

    response = client.post(f"{base_url}/favoritemusic/", json={'user_id': 122, 'query': 'http://some-url.com'})
    data = response.json()
    assert response.status_code == 202
    assert data['counter'] == 2  # update user-music note

    response = client.post(f"{base_url}/favoritemusic/", json={'user_id': 122, 'query': 'http://some-another-url.com'})
    assert response.status_code == 201  # create another user-music note


def test_get_music(client: TestClient):
    response = client.get(f"{base_url}/favoritemusic/122")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 2
