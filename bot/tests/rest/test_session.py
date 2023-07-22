import datetime

from fastapi.testclient import TestClient

from bot.api.rest.base import base_url
from bot.api.rest.v1.dependencies import default_period

TEST_CHANNEL_ID = 1
TEST_USER_ID = 112
TEST_MSG_ID = 326


def test_post_sessions(client: TestClient, post_sessions):
    response = client.post(f"{base_url}/session/", json={'channel_id': 'Invalid data'})
    assert response.status_code == 422


def test_all_sessions(client: TestClient):
    response = client.get(f"{base_url}/session/")
    data_without_params = response.json()

    response = client.get(f"{base_url}/session/", params=default_period())
    data_with_default_params = response.json()

    assert isinstance(data_without_params, list) and data_without_params == data_with_default_params

    response = client.get(f"{base_url}/session/", params=default_period(begin=datetime.datetime(2000, 1, 1, 3)))
    data_with_params = response.json()
    assert len(data_with_params) == 3


def test_unclosed_sessions(client: TestClient):
    response = client.get(f"{base_url}/session/unclosed/")
    unclosed_sessions = response.json()  # last 3 channels
    assert len(unclosed_sessions) == 3


def test_get_session(client: TestClient):
    response = client.get(f"{base_url}/session/{TEST_CHANNEL_ID}")
    data = response.json()

    assert response.status_code == 200
    assert data['channel_id'] == TEST_CHANNEL_ID
    assert data["name"] == "1"
    assert data["begin"] is not None

    response = client.get(f"{base_url}/session/by_msg/{data['message_id']}")
    data = response.json()

    assert response.status_code == 200
    assert data['channel_id'] == TEST_CHANNEL_ID
    assert data["name"] == "1"
    assert data["begin"] is not None


def test_patch_session(client: TestClient):
    new_name = 'Modified'
    response = client.patch(f"{base_url}/session/{TEST_CHANNEL_ID}", json={'name': new_name})
    data = response.json()
    assert data['name'] == new_name
    response = client.patch(f"{base_url}/session/{TEST_CHANNEL_ID}", json={'name': '1'})
    data = response.json()
    assert data['name'] == '1'


def test_add_session_member(client: TestClient, post_user):
    response = client.post(f"{base_url}/session/{TEST_CHANNEL_ID}/members/{TEST_USER_ID}")
    data = response.json()

    assert response.status_code == 201
    assert isinstance(data['id'], int)


def test_get_session_members(client: TestClient):
    response = client.get(f"{base_url}/session/{TEST_CHANNEL_ID}/members/")
    data = response.json()

    assert response.status_code == 200
    assert isinstance(data, list) and len(data) == 1


def test_get_session_leadership(client: TestClient):
    response = client.get(f"{base_url}/session/{TEST_MSG_ID}/leadership/")
    data = response.json()
    assert response.status_code == 200
    assert isinstance(data, list) and len(data) == 2


def test_get_session_presence(client: TestClient):
    response = client.get(f"{base_url}/session/{TEST_MSG_ID}/prescence/")
    data = response.json()
    assert response.status_code == 200
    assert isinstance(data, list) and len(data) == 1


def test_get_session_activities(client: TestClient):
    response = client.get(f"{base_url}/session/{TEST_MSG_ID}/activities/")
    data = response.json()
    assert response.status_code == 200
    assert isinstance(data, list) and len(data) == 1
