import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def get_user_112(client: AsyncClient):
    return await client.get(f"/user/112")


@pytest.mark.asyncio
async def test_post_user(client: AsyncClient):
    response = await client.post(
        f"/user",
        json={'id': 113, 'name': 'USER-2', 'default_sess_name': None}
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_get_user(client: AsyncClient, post_users):
    response = await get_user_112(client)
    assert response.status_code == 200

    response = await client.get(f"/user/543")
    # not existed user example, will return 404
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_patch_user(client: AsyncClient, post_users):
    response = await client.patch(
        f"/user/112",
        json={'name': 'NicknameUpdate', 'default_sess_name': 'New session name'}
    )
    data = response.json()
    assert response.status_code == 200
    assert data['name'] == 'NicknameUpdate'
    assert data['default_sess_name'] == 'New session name'


@pytest.mark.asyncio
async def test_get_all_users(client: AsyncClient, post_users):
    response = await client.get(f"/user")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_user_sessions(client: AsyncClient, add_session_member):
    response = await client.get(f"/user/112/sessions")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 1


@pytest.mark.asyncio
async def test_get_user_activities(client: AsyncClient, post_activity,
                                   end_activity):
    response = await client.get(f"/user/112/activities")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 1


@pytest.mark.asyncio
async def test_get_user_concrete_activities(
    client: AsyncClient,
    post_activity,
    end_activity
):
    app_id = 12345
    response = await client.get(f"/user/112/activities/{app_id}")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 1


@pytest.mark.asyncio
async def test_get_user_activities_duration(
    client: AsyncClient,
    post_activity,
    end_activity
):
    response = await client.get("/user/112/activities/duration/")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 1


@pytest.mark.asyncio
async def test_get_user_concrete_activity_duration(
    client: AsyncClient,
    post_role,
    post_activity,
    end_activity
):
    role_id = 20_001
    response = await client.get(f"/user/112/activities/duration/{role_id}")
    data = response.json()

    assert response.status_code == 200
    assert data['seconds'] == 6_354
