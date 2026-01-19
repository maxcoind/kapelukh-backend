from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from .config import settings
from .logger import get_logger

log = get_logger("database")


def getEngine(database_url: str) -> AsyncEngine:
    """Create and return an async SQLAlchemy engine."""
    return create_async_engine(database_url, echo=True, future=True)


async def create_db_and_tables(async_engine: AsyncEngine):
    """Create database and all defined tables."""
    log.info("Creating database and tables...")
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


def get_engine_singleton():
    engine = None

    def inner():
        nonlocal engine
        if engine is None:
            log.info(f"Connecting to database: ${settings.db.url}")
            engine = getEngine(settings.db.url)
        return engine

    return inner


get_engine = get_engine_singleton()


def get_async_session_singleton():
    session_factory = None

    def inner():
        nonlocal session_factory
        if session_factory is None:
            session_factory = async_sessionmaker(
                bind=get_engine(), expire_on_commit=False, class_=AsyncSession
            )
        return session_factory

    return inner


get_async_session = get_async_session_singleton()


async def getDbSession() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to provide a session per request."""
    async with get_async_session()() as session:
        try:
            yield session
        finally:
            # The context manager 'async with' handles closing automatically,
            # but we can explicitly ensure cleanup here if needed.
            await session.close()
