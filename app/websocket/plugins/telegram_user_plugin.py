from typing import Type
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.telegram_user import TelegramUser
from app.websocket.plugin_system import ModelPlugin
from app.schemas.websocket import SubscriptionParams


class TelegramUserPlugin(ModelPlugin):
    """Plugin for TelegramUser model."""

    topic: str = "telegram_user"
    model_class: Type[SQLModel] = TelegramUser
    primary_key: str = "id"

    async def to_dict(self, instance: TelegramUser) -> dict:
        """Convert telegram user instance to dictionary."""
        return {
            "id": instance.id,
            "telegram_id": instance.telegram_id,
            "username": instance.username,
            "first_name": instance.first_name,
            "last_name": instance.last_name,
            "language_code": instance.language_code,
            "is_active": instance.is_active,
            "is_bot": instance.is_bot,
            "created_at": instance.created_at.isoformat()
            if instance.created_at
            else None,
            "updated_at": instance.updated_at.isoformat()
            if instance.updated_at
            else None,
            "last_interaction_at": instance.last_interaction_at.isoformat()
            if instance.last_interaction_at
            else None,
        }

    async def fetch_initial_data(
        self, session: AsyncSession, params: SubscriptionParams
    ) -> dict:
        """Fetch initial telegram users for subscription."""
        # Simple query without filtering
        query = select(TelegramUser).order_by(TelegramUser.created_at.desc()).limit(100)
        result = await session.execute(query)
        users = result.scalars().all()

        return {"items": [await self.to_dict(u) for u in users], "total": len(users)}
