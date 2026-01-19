from typing import Protocol, Type, List, Dict, Optional, runtime_checkable
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from app.schemas.websocket import SubscriptionParams


@runtime_checkable
class ModelPlugin(Protocol):
    """Protocol for models that can be subscribed via WebSocket."""

    topic: str
    model_class: Type[SQLModel]
    primary_key: str = "id"

    async def to_dict(self, instance) -> dict:
        """Convert model instance to dictionary for JSON serialization."""
        ...

    async def fetch_initial_data(
        self, session: AsyncSession, params: SubscriptionParams
    ) -> dict:
        """
        Fetch initial data for subscription.
        Returns dict with 'items' (list of records) and 'total' (count).
        """
        ...


class ModelRegistry:
    """Registry for model plugins."""

    def __init__(self):
        self._plugins: Dict[str, ModelPlugin] = {}

    def register(self, plugin: ModelPlugin) -> None:
        """Register a model plugin."""
        if not isinstance(plugin, ModelPlugin):
            raise TypeError(f"Plugin {plugin} does not implement ModelPlugin protocol")

        if plugin.topic in self._plugins:
            raise ValueError(f"Topic '{plugin.topic}' is already registered")

        self._plugins[plugin.topic] = plugin

    def get(self, topic: str) -> Optional[ModelPlugin]:
        """Get plugin by topic."""
        return self._plugins.get(topic)

    def get_all_topics(self) -> List[str]:
        """Get all registered topics."""
        return list(self._plugins.keys())

    def is_valid_topic(self, topic: str) -> bool:
        """Check if topic is registered."""
        return topic in self._plugins

    def get_all_plugins(self) -> Dict[str, ModelPlugin]:
        """Get all registered plugins."""
        return self._plugins.copy()


# Global registry instance
model_registry = ModelRegistry()
