from typing import Literal
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession


class ModelEventHelper:
    """Helper for triggering model events from API endpoints."""

    @staticmethod
    async def trigger_event(
        db: AsyncSession,
        connection_manager,
        topic: str,
        event_type: Literal["created", "updated", "deleted"],
        instance: SQLModel,
        to_dict_func: callable,
    ) -> None:
        """
        Trigger a model event.

        Args:
            db: Database session
            connection_manager: WebSocket connection manager
            topic: Model topic
            event_type: Event type (created, updated, deleted)
            instance: Model instance
            to_dict_func: Function to convert instance to dict
        """
        from app.websocket.event_bus import get_event_processor

        record_id = getattr(instance, "id")
        record_data = to_dict_func(instance)

        event_processor = get_event_processor(db, connection_manager)
        await event_processor.publish_model_event(
            topic=topic,
            event_type=event_type,
            record_id=record_id,
            record_data=record_data,
        )
