from typing import Optional, Callable, Dict, Any, Awaitable
from abc import ABC, abstractmethod
import asyncio
import json
from websockets.asyncio.client import ClientConnection
from websockets.exceptions import (
    ConnectionClosed,
    ConnectionClosedOK,
    ConnectionClosedError,
    InvalidURI,
    InvalidHandshake,
)

from app.services.base import (
    BaseExternalService,
    ServiceConnectionError,
    ServiceTimeoutError,
)
from app.logger import get_logger

logger = get_logger("ws_service")


class WebSocketMessageHandler(ABC):
    """Abstract handler for processing incoming WebSocket messages."""

    @abstractmethod
    async def handle_message(self, message: str | bytes) -> None:
        """
        Process an incoming WebSocket message.

        Args:
            message: The received message (str for text, bytes for binary)
        """
        pass


class WebSocketService(BaseExternalService):
    """Abstract WebSocket service client with connection management and message handling."""

    def __init__(
        self,
        base_url: str,
        endpoint: str = "/",
        timeout: float = 30.0,
        max_retries: int = 3,
        verify_ssl: bool = True,
        api_key: Optional[str] = None,
        ping_interval: float = 20.0,
        ping_timeout: float = 20.0,
        close_timeout: float = 10.0,
        max_queue_size: int = 1024,
    ):
        super().__init__(base_url, timeout, max_retries, verify_ssl, api_key)
        self.endpoint = endpoint
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.close_timeout = close_timeout
        self.max_queue_size = max_queue_size
        self._connection: Optional[ClientConnection] = None
        self._message_handlers: list[Callable[[str | bytes], Awaitable[None]]] = []
        self._is_connected = False
        self._reconnect_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    @property
    def ws_url(self) -> str:
        """Get the full WebSocket URL."""
        protocol = "wss://" if self.verify_ssl else "ws://"
        return f"{protocol}{self.base_url.replace('https://', '').replace('http://', '')}{self.endpoint}"

    @abstractmethod
    async def on_connect(self) -> None:
        """
        Called when the WebSocket connection is established.
        Override this method to perform initial setup.
        """
        pass

    @abstractmethod
    async def on_disconnect(self) -> None:
        """
        Called when the WebSocket connection is closed.
        Override this method to perform cleanup.
        """
        pass

    @abstractmethod
    async def on_message(self, message: str | bytes) -> None:
        """
        Called for each incoming message.
        Override this method to process messages.

        Args:
            message: The received message (str for text, bytes for binary)
        """
        pass

    async def on_error(self, error: Exception) -> None:
        """
        Called when an error occurs.
        Override this method to handle errors.

        Args:
            error: The exception that occurred
        """
        logger.error(f"WebSocket error: {error}")

    def add_message_handler(
        self, handler: Callable[[str | bytes], Awaitable[None]]
    ) -> None:
        """
        Add a custom message handler.

        Args:
            handler: Async function that takes message and returns None
        """
        self._message_handlers.append(handler)
        logger.debug(f"Added message handler: {handler.__name__}")

    def remove_message_handler(
        self, handler: Callable[[str | bytes], Awaitable[None]]
    ) -> None:
        """
        Remove a custom message handler.

        Args:
            handler: The handler function to remove
        """
        if handler in self._message_handlers:
            self._message_handlers.remove(handler)
            logger.debug(f"Removed message handler: {handler.__name__}")

    async def connect(self) -> None:
        """
        Establish WebSocket connection with automatic reconnection.
        """
        await super().connect()
        await self._connect_with_retry()

    async def _connect_with_retry(self) -> None:
        """
        Connect to WebSocket with retry logic.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    f"Connecting to WebSocket {self.ws_url} (attempt {attempt}/{self.max_retries})"
                )

                extra_headers = self._get_headers() if self.api_key else {}

                self._connection = await asyncio.wait_for(
                    ClientConnection.connect(
                        self.ws_url,
                        ping_interval=self.ping_interval,
                        ping_timeout=self.ping_timeout,
                        close_timeout=self.close_timeout,
                        max_queue=self.max_queue_size,
                        extra_headers=extra_headers,
                    ),
                    timeout=self.timeout,
                )

                self._is_connected = True
                self._stop_event.clear()
                logger.info(f"WebSocket connected to {self.ws_url}")

                await self.on_connect()

                self._receive_task = asyncio.create_task(self._receive_messages())
                self._reconnect_task = asyncio.create_task(self._monitor_connection())

                return

            except asyncio.TimeoutError as e:
                logger.error(
                    f"Connection timeout (attempt {attempt}/{self.max_retries})"
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(min(2**attempt, 10))
                else:
                    await self.on_error(
                        ServiceTimeoutError(f"Connection timeout after {self.timeout}s")
                    )
                    raise ServiceTimeoutError(
                        f"Failed to connect after {self.max_retries} attempts"
                    ) from e

            except (InvalidURI, InvalidHandshake) as e:
                logger.error(f"Invalid WebSocket URL or handshake: {e}")
                await self.on_error(
                    ServiceConnectionError(f"Invalid WebSocket configuration: {e}")
                )
                raise ServiceConnectionError(
                    f"Invalid WebSocket configuration: {e}"
                ) from e

            except Exception as e:
                logger.error(
                    f"Connection failed (attempt {attempt}/{self.max_retries}): {e}"
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(min(2**attempt, 10))
                else:
                    await self.on_error(e)
                    raise ServiceConnectionError(
                        f"Failed to connect after {self.max_retries} attempts"
                    ) from e

    async def _monitor_connection(self) -> None:
        """
        Monitor connection health and trigger reconnection if needed.
        """
        while self._is_connected and not self._stop_event.is_set():
            try:
                if self._connection and self._connection.closed:
                    logger.warning("WebSocket connection closed unexpectedly")
                    await self._reconnect()
                    break

                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error monitoring connection: {e}")
                await self.on_error(e)
                break

    async def _reconnect(self) -> None:
        """
        Reconnect to WebSocket after disconnection.
        """
        if self._is_connected:
            logger.info("Attempting to reconnect...")
            await self.disconnect()
            await asyncio.sleep(2)
            await self._connect_with_retry()

    async def _receive_messages(self) -> None:
        """
        Continuously receive and handle incoming messages.
        """
        try:
            while self._is_connected and not self._stop_event.is_set():
                try:
                    if self._connection is None or self._connection.closed:
                        break

                    message = await asyncio.wait_for(
                        self._connection.recv(),
                        timeout=self.timeout,
                    )

                    logger.debug(
                        f"Received message: {message[:100] if len(str(message)) > 100 else message}"
                    )

                    await self.on_message(message)

                    for handler in self._message_handlers:
                        try:
                            await handler(message)
                        except Exception as e:
                            logger.error(
                                f"Error in message handler {handler.__name__}: {e}"
                            )

                except asyncio.TimeoutError:
                    logger.debug("Receive timeout, continuing...")
                    continue

                except ConnectionClosedOK:
                    logger.info("WebSocket closed normally")
                    break

                except ConnectionClosedError as e:
                    logger.warning(f"WebSocket closed with error: {e}")
                    await self.on_error(e)
                    if not self._stop_event.is_set():
                        await self._reconnect()
                    break

                except Exception as e:
                    logger.error(f"Error receiving message: {e}")
                    await self.on_error(e)
                    break

        except asyncio.CancelledError:
            logger.debug("Receive task cancelled")
        except Exception as e:
            logger.error(f"Fatal error in receive loop: {e}")
            await self.on_error(e)

    async def send(self, message: str | bytes | Dict[str, Any]) -> None:
        """
        Send a message through the WebSocket.

        Args:
            message: Message to send (str, bytes, or dict for JSON)

        Raises:
            ServiceConnectionError: If not connected
        """
        if (
            not self._is_connected
            or self._connection is None
            or self._connection.closed
        ):
            raise ServiceConnectionError("WebSocket is not connected")

        try:
            if isinstance(message, dict):
                message = json.dumps(message)

            await self._connection.send(message)
            logger.debug(
                f"Sent message: {message[:100] if len(str(message)) > 100 else message}"
            )

        except ConnectionClosed:
            logger.warning("Connection closed while sending")
            await self.on_error(ServiceConnectionError("Connection closed"))
            raise ServiceConnectionError("Connection closed") from None
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            await self.on_error(e)
            raise

    async def send_json(self, data: Dict[str, Any]) -> None:
        """
        Send a JSON message.

        Args:
            data: Dictionary to send as JSON
        """
        await self.send(data)

    async def disconnect(self) -> None:
        """
        Close the WebSocket connection gracefully.
        """
        self._is_connected = False
        self._stop_event.set()

        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass

        if self._connection and not self._connection.closed:
            try:
                await self._connection.close()
                logger.info("WebSocket connection closed")
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")

        await self.on_disconnect()
        await super().close()

    async def close(self) -> None:
        """Alias for disconnect() for compatibility with BaseExternalService."""
        await self.disconnect()

    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is currently connected."""
        return (
            self._is_connected
            and self._connection is not None
            and not self._connection.closed
        )

    async def health_check(self) -> bool:
        """
        Check if WebSocket service is healthy.

        Returns:
            True if connected and healthy, False otherwise
        """
        try:
            if not self.is_connected:
                return False

            await self._connection.ping()
            return True

        except Exception as e:
            logger.error(f"WebSocket health check failed: {e}")
            return False
