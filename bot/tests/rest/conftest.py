import pytest

from fastapi.testclient import TestClient
from sqlmodel import Session

from _engine import engine
from bot.api.rest.base import app
from bot.api.rest.base import base_url
from bot.api.rest.database import get_session


@pytest.fixture(name="session")
def session_fixture():
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def post_user(client: TestClient):
    try:
        response = client.post(f"{base_url}/user/",
                               json={'id': 112, 'name': 'USER',
                                     'default_sess_name': 'Session name'})
        assert response.status_code == 201
    except:
        pass


@pytest.fixture
def post_activityinfo(client: TestClient):
    try:
        response = client.post(f"{base_url}/activityinfo/",
                               json={'app_id': 12345, 'app_name': 'AppName',
                                     'icon_url': 'url'})
    except:
        response = client.get(f"{base_url}/activityinfo/12345")
    return response


@pytest.fixture
def post_sessions(client: TestClient):
    for x in range(1, 6):
        try:
            response = client.post(f"{base_url}/session/",
                                   json={'channel_id': x,
                                         'leader_id': 111 + x - 1,
                                         'creator_id': 111 + x % 2,
                                         'message_id': 321 + 5 * x,
                                         'begin': f'2000-01-01 0{x}:00:00',
                                         'end': f'2000-01-01 0{x + 1}:00:00' if x < 3 else None,
                                         'name': f'{x}' * x})
            assert response.status_code == 201
        except:
            return
