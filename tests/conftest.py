import pytest_asyncio
from collections.abc import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.main import app


@pytest_asyncio.fixture
async def auth_headers(async_client: AsyncClient) -> dict:
    """Create authorization headers for authenticated requests."""
    response = await async_client.post(
        "/api/v1/auth/login", data={"username": "admin", "password": "admin"}
    )
    assert response.status_code == 200
    tokens = response.json()
    access_token = tokens["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture
async def async_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create in-memory SQLite engine for tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(
    async_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """Create async database session for tests."""
    async_session = async_sessionmaker(
        bind=async_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def db_session(async_session: AsyncSession) -> AsyncSession:
    """Alias for async_session fixture."""
    return async_session


@pytest_asyncio.fixture
async def async_client(async_engine: AsyncEngine) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client with test database."""

    async def get_test_session():
        async_session = async_sessionmaker(
            bind=async_engine, expire_on_commit=False, class_=AsyncSession
        )
        async with async_session() as session:
            yield session

    from app.database import getDbSession

    app.dependency_overrides[getDbSession] = get_test_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def cleanup_global_engine():
    """Dispose of global database engine after all tests."""
    from app.database import get_engine

    engine = get_engine()
    yield
    await engine.dispose()
