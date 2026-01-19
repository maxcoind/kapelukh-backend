from typing import Type
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.survey import Survey
from app.websocket.plugin_system import ModelPlugin
from app.schemas.websocket import SubscriptionParams


class SurveyPlugin(ModelPlugin):
    """Plugin for Survey model."""

    topic: str = "survey"
    model_class: Type[SQLModel] = Survey
    primary_key: str = "id"

    async def to_dict(self, instance: Survey) -> dict:
        """Convert survey instance to dictionary."""
        return {
            "id": instance.id,
            "user_id": instance.user_id,
            "full_name": instance.full_name,
            "super_powers": instance.super_powers,
            "birth_date": instance.birth_date,
            "traits_to_improve": instance.traits_to_improve,
            "to_buy": instance.to_buy,
            "to_sell": instance.to_sell,
            "service": instance.service,
            "material_goal": instance.material_goal,
            "social_goal": instance.social_goal,
            "spiritual_goal": instance.spiritual_goal,
            "created_at": instance.created_at.isoformat()
            if instance.created_at
            else None,
            "updated_at": instance.updated_at.isoformat()
            if instance.updated_at
            else None,
        }

    async def fetch_initial_data(
        self, session: AsyncSession, params: SubscriptionParams
    ) -> dict:
        """Fetch initial surveys for subscription."""
        query = select(Survey).order_by(Survey.created_at.desc()).limit(100)
        result = await session.execute(query)
        surveys = result.scalars().all()

        return {
            "items": [await self.to_dict(s) for s in surveys],
            "total": len(surveys),
        }
