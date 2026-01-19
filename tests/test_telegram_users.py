import pytest
from httpx import AsyncClient

from app.models.telegram_user import TelegramUser


@pytest.mark.asyncio
async def test_create_telegram_user(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/v1/telegram-users/",
        json={
            "telegram_id": 123456789,
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "language_code": "en",
            "is_active": True,
            "is_bot": False,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["telegram_id"] == 123456789
    assert data["username"] == "testuser"
    assert data["first_name"] == "Test"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_duplicate_telegram_user(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
):
    user = TelegramUser(
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/telegram-users/",
        json={
            "telegram_id": 123456789,
            "username": "anotheruser",
            "first_name": "Another",
        },
        headers=auth_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_telegram_user(client: AsyncClient, auth_headers: dict, db_session):
    user = TelegramUser(
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    response = await client.get(
        f"/api/v1/telegram-users/{user.telegram_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["telegram_id"] == 123456789


@pytest.mark.asyncio
async def test_get_telegram_user_not_found(client: AsyncClient, auth_headers: dict):
    response = await client.get(
        "/api/v1/telegram-users/999999999",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_telegram_users(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
):
    for i in range(5):
        user = TelegramUser(
            telegram_id=123456789 + i,
            username=f"user{i}",
            first_name=f"User{i}",
            is_active=True if i < 3 else False,
        )
        db_session.add(user)
    await db_session.commit()

    response = await client.get(
        "/api/v1/telegram-users/?skip=0&limit=10&is_active=true",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_get_telegram_users_with_username_filter(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
):
    user = TelegramUser(
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.get(
        "/api/v1/telegram-users/?username=test",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["username"] == "testuser"


@pytest.mark.asyncio
async def test_update_telegram_user(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
):
    user = TelegramUser(
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    response = await client.put(
        f"/api/v1/telegram-users/{user.telegram_id}",
        json={"first_name": "Updated"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Updated"


@pytest.mark.asyncio
async def test_soft_delete_telegram_user(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
):
    user = TelegramUser(
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    response = await client.delete(
        f"/api/v1/telegram-users/{user.telegram_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    await db_session.refresh(user)
    assert user.is_active is False


@pytest.mark.asyncio
async def test_update_last_interaction(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
):
    user = TelegramUser(
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    response = await client.patch(
        f"/api/v1/telegram-users/{user.telegram_id}/last-interaction",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["last_interaction_at"] is not None


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    response = await client.get("/api/v1/telegram-users/")
    assert response.status_code == 401
