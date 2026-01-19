from typing import Dict, List, Callable, Optional, Literal
from datetime import datetime, timezone
from sqlmodel.ext.asyncio.session import AsyncSession
from app.websocket.manager import ConnectionManager
from app.crud.websocket import get_subscriptions_by_topic


class ModelEvent:
    """Represents a model event (created, updated, deleted)."""

    def __init__(
        self,
        event_type: Literal["created", "updated", "deleted"],
        topic: str,
        record_id: int,
        record_data: dict,
        metadata: Optional[dict] = None,
    ):
        self.event_type = event_type
        self.topic = topic
        self.record_id = record_id
        self.record_data = record_data
        self.metadata = metadata or {}
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        """Convert event to dictionary for JSON serialization."""
        return {
            "event_type": self.event_type,
            "topic": self.topic,
            "record_id": self.record_id,
            "record_data": self.record_data,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


class EventBus:
    """Central publish/subscribe system for internal services."""

    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}

    async def publish(self, topic: str, event: ModelEvent) -> None:
        """Publish an event to all subscribers of a topic."""
        handlers = self.subscribers.get(topic, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                print(f"Error in event handler for topic {topic}: {e}")

    async def subscribe(self, topic: str, handler: Callable) -> None:
        """Subscribe a handler to a topic."""
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(handler)

    async def unsubscribe(self, topic: str, handler: Callable) -> None:
        """Unsubscribe a handler from a topic."""
        if topic in self.subscribers:
            self.subscribers[topic] = [
                h for h in self.subscribers[topic] if h != handler
            ]

    def clear_subscribers(self, topic: Optional[str] = None) -> None:
        """Clear all subscribers or subscribers for a specific topic."""
        if topic:
            self.subscribers.pop(topic, None)
        else:
            self.subscribers.clear()


class EventProcessor:
    """Processes model events and broadcasts to WebSocket subscribers."""

    def __init__(self, db: AsyncSession, connection_manager: ConnectionManager):
        self.db = db
        self.connection_manager = connection_manager

    async def publish_model_event(
        self,
        topic: str,
        event_type: Literal["created", "updated", "deleted"],
        record_id: int,
        record_data: dict,
    ) -> None:
        """Publish a model event via event bus."""
        event = ModelEvent(
            event_type=event_type,
            topic=topic,
            record_id=record_id,
            record_data=record_data,
        )
        await self.broadcast_to_subscribers(topic, event)

    async def broadcast_to_subscribers(self, topic: str, event: ModelEvent) -> None:
        """Broadcast an event to all WebSocket subscribers for a topic."""
        subscriptions = await get_subscriptions_by_topic(session=self.db, topic=topic)

        for subscription in subscriptions:
            session = self.connection_manager.get_client_session(
                subscription.subscription_id
            )

            if session:
                message = {
                    "type": "event",
                    "topic": topic,
                    "event_type": event.event_type,
                    "subscription_id": subscription.subscription_id,
                    "data": event.record_data,
                    "timestamp": event.timestamp.isoformat(),
                }
                await self.connection_manager.send_message(
                    subscription.subscription_id, message
                )
