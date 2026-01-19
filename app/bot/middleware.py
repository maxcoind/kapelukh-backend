from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session


class DBSessionMiddleware(BaseMiddleware):
    """Middleware to provide database sessions to bot handlers.

    When a session is already provided in data (e.g., from FastAPI webhook),
    it will be used. Otherwise, a new session is created.
    """

    async def __call__(
        self,
        handler,
        event: TelegramObject,
        data: dict,
    ) -> None:
        if "session" in data and isinstance(data["session"], AsyncSession):
            session = data["session"]
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
        else:
            async with get_async_session()() as session:
                data["session"] = session
                try:
                    result = await handler(event, data)
                    await session.commit()
                    return result
                except Exception:
                    await session.rollback()
                    raise
