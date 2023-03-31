import pytest
from fastapi.testclient import TestClient

from api.rest.base import base_url


def get_user_112(client):
    return client.get(f"{base_url}/user/112")


@pytest.fixture
def post_user(client: TestClient):
    try:
        response = client.post(f"{base_url}/user/", json={'id': 112, 'name': 'USER',
                                                          'default_sess_name': 'Session name'})
        assert response.status_code == 201
    except:
        pass


def test_post_user(client: TestClient):
    response = client.post(f"{base_url}/user/", json={'id': 113, 'name': 'USER-2',
                                                      'default_sess_name': None})
    assert response.status_code == 201


def test_get_user(client: TestClient, post_user):
    response = get_user_112(client)
    assert response.status_code == 200

    response = client.get(f"{base_url}/user/543")  # not existed user example, will return 404
    assert response.status_code == 404


def test_patch_user(client: TestClient, post_user):
    response = client.patch(f"{base_url}/user/112", json={'name': 'NicknameUpdate',
                                                          'default_sess_name': 'New session name'})
    data = response.json()
    assert response.status_code == 200
    assert data['name'] == 'NicknameUpdate'
    assert data['default_sess_name'] == 'New session name'


def test_get_all_users(client: TestClient):
    response = client.get(f"{base_url}/user/")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 2


def test_get_user_sessions(client: TestClient):
    response = client.get(f"{base_url}/user/112/sessions/")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 1


def test_get_user_activities(client: TestClient):
    response = client.get(f"{base_url}/user/112/activities/")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 1


def test_get_user_concrete_activities(client: TestClient):
    app_id = 12345
    response = client.get(f"{base_url}/user/112/activities/{app_id}")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 1


def test_get_user_activities_duration(client: TestClient):
    response = client.get(f"{base_url}/user/112/activities/duration/")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 1


def test_get_user_concrete_activity_duration(client: TestClient):
    role_id = 20_001
    response = client.get(f"{base_url}/user/112/activities/duration/{role_id}")
    data = response.json()

    assert response.status_code == 200
    assert data['seconds'] == 6_354
