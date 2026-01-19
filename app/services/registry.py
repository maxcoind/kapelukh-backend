from typing import Optional, Dict, Type

from app.services.base import BaseExternalService
from app.services.rest_service import RESTService
from app.services.ws_service import WebSocketService
from app.logger import get_logger

logger = get_logger("service_registry")


class ServiceRegistry:
    """
    Registry for managing external service client instances.
    Provides dependency injection for FastAPI routes.
    """

    _clients: Dict[str, BaseExternalService] = {}

    @classmethod
    def register_client(cls, name: str, client: BaseExternalService) -> None:
        """
        Register a service client instance.

        Args:
            name: Unique name for the client
            client: The client instance to register
        """
        if name in cls._clients:
            logger.warning(f"Client '{name}' already registered, overwriting")

        cls._clients[name] = client
        logger.info(f"Registered service client: {name}")

    @classmethod
    def get_client(cls, name: str) -> Optional[BaseExternalService]:
        """
        Get a registered service client.

        Args:
            name: Name of the client to retrieve

        Returns:
            The client instance if found, None otherwise
        """
        return cls._clients.get(name)

    @classmethod
    def unregister_client(cls, name: str) -> None:
        """
        Unregister a service client.

        Args:
            name: Name of the client to unregister
        """
        if name in cls._clients:
            client = cls._clients.pop(name)
            logger.info(f"Unregistered service client: {name}")

    @classmethod
    async def close_all(cls) -> None:
        """Close all registered clients."""
        for name, client in cls._clients.items():
            try:
                await client.close()
            except Exception as e:
                logger.error(f"Error closing client {name}: {e}")
        cls._clients.clear()
        logger.info("All service clients closed")


def create_rest_client(
    name: str,
    base_url: str,
    timeout: float = 30.0,
    max_retries: int = 3,
    verify_ssl: bool = True,
    api_key: Optional[str] = None,
    endpoint_base: str = "",
) -> RESTService:
    """
    Factory function to create and register a REST service client.

    Args:
        name: Unique name for the client
        base_url: Base URL of the REST API
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        verify_ssl: Whether to verify SSL certificates
        api_key: Optional API key for authentication
        endpoint_base: Optional base path for endpoints (e.g., "/api/v1")

    Returns:
        The created RESTService instance
    """
    client = RESTService(
        base_url=base_url,
        timeout=timeout,
        max_retries=max_retries,
        verify_ssl=verify_ssl,
        api_key=api_key,
    )

    if endpoint_base:
        client.endpoint_base = endpoint_base

    ServiceRegistry.register_client(name, client)
    return client


def create_ws_client(
    name: str,
    base_url: str,
    endpoint: str = "/",
    timeout: float = 30.0,
    max_retries: int = 3,
    verify_ssl: bool = True,
    api_key: Optional[str] = None,
    ping_interval: float = 20.0,
    ping_timeout: float = 20.0,
) -> Type[WebSocketService]:
    """
    Factory function to create and register a WebSocket service client.

    Note: This returns a WebSocketService class, not an instance.
    You must create a concrete subclass that implements the abstract methods.

    Args:
        name: Unique name for the client
        base_url: Base URL of the WebSocket server
        endpoint: WebSocket endpoint path
        timeout: Connection timeout in seconds
        max_retries: Maximum number of retry attempts
        verify_ssl: Whether to verify SSL certificates
        api_key: Optional API key for authentication
        ping_interval: Interval between ping frames in seconds
        ping_timeout: Timeout for pong response in seconds

    Returns:
        A WebSocketService subclass configured with the provided settings
    """

    class ConfiguredWebSocketService(WebSocketService):
        def __init__(self):
            super().__init__(
                base_url=base_url,
                endpoint=endpoint,
                timeout=timeout,
                max_retries=max_retries,
                verify_ssl=verify_ssl,
                api_key=api_key,
                ping_interval=ping_interval,
                ping_timeout=ping_timeout,
            )

        async def on_connect(self):
            pass

        async def on_disconnect(self):
            pass

        async def on_message(self, message: str | bytes):
            pass

    ServiceRegistry.register_client(name, ConfiguredWebSocketService())
    return ConfiguredWebSocketService


def get_service_client(name: str) -> BaseExternalService:
    """
    FastAPI dependency to get a registered service client.

    Args:
        name: Name of the registered client

    Returns:
        The client instance

    Raises:
        ValueError: If client is not registered
    """
    client = ServiceRegistry.get_client(name)
    if client is None:
        raise ValueError(f"Service client '{name}' is not registered")
    return client


def get_rest_client(name: str) -> RESTService:
    """
    FastAPI dependency to get a registered REST service client.

    Args:
        name: Name of the registered REST client

    Returns:
        The RESTService instance

    Raises:
        ValueError: If client is not registered or is not a REST client
    """
    client = get_service_client(name)
    if not isinstance(client, RESTService):
        raise ValueError(f"Client '{name}' is not a REST service client")
    return client


def get_ws_client(name: str) -> WebSocketService:
    """
    FastAPI dependency to get a registered WebSocket service client.

    Args:
        name: Name of the registered WebSocket client

    Returns:
        The WebSocketService instance

    Raises:
        ValueError: If client is not registered or is not a WebSocket client
    """
    client = get_service_client(name)
    if not isinstance(client, WebSocketService):
        raise ValueError(f"Client '{name}' is not a WebSocket service client")
    return client


async def initialize_services():
    """
    Initialize all service clients from configuration.
    Call this during application startup.
    """
    logger.info("Initializing service clients...")

    # Example: Initialize services from settings
    # You can add configuration in app/config.py and initialize here

    # Example REST client
    # if settings.EXTERNAL_API_URL:
    #     create_rest_client(
    #         name="external_api",
    #         base_url=settings.EXTERNAL_API_URL,
    #         api_key=settings.EXTERNAL_API_KEY,
    #         timeout=settings.EXTERNAL_API_TIMEOUT,
    #     )

    # Example WebSocket client
    # if settings.EXTERNAL_WS_URL:
    #     create_ws_client(
    #         name="external_ws",
    #         base_url=settings.EXTERNAL_WS_URL,
    #         api_key=settings.EXTERNAL_WS_KEY,
    #     )

    logger.info(f"Initialized {len(ServiceRegistry._clients)} service clients")


async def shutdown_services():
    """
    Shutdown all service clients.
    Call this during application shutdown.
    """
    logger.info("Shutting down service clients...")
    await ServiceRegistry.close_all()
