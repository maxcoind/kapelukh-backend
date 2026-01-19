import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    result = response.json()
    assert "status" in result
    assert "database" in result
    assert "telegram" in result
