import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_authentication_flow(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/login", data={"username": "admin", "password": "admin"}
    )
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"

    access_token = tokens["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}

    response = await async_client.get("/api/v1/payments/", headers=headers)
    assert response.status_code == 200

    response = await async_client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == "admin"


@pytest.mark.asyncio
async def test_unauthorized_access(async_client: AsyncClient):
    response = await async_client.get("/api/v1/payments/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_login(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/login", data={"username": "wrong", "password": "wrong"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(async_client: AsyncClient):
    login_response = await async_client.post(
        "/api/v1/auth/login", data={"username": "admin", "password": "admin"}
    )
    tokens = login_response.json()
    refresh_token = tokens["refresh_token"]

    refresh_response = await async_client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refresh_response.status_code == 200
    new_tokens = refresh_response.json()
    assert "access_token" in new_tokens
    assert new_tokens["refresh_token"] == refresh_token
