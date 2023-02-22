import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from _engine import engine
from api.rest.base import app
from api.rest.database import get_session


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
