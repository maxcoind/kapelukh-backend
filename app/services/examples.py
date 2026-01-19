"""
Example usage of the external service clients.

This file demonstrates how to use the REST and WebSocket service clients
for integrating with external web services.
"""

from app.services import (
    RESTService,
    WebSocketService,
    get_rest_client,
)
from fastapi import Depends, BackgroundTasks
from typing import Dict, Any


# ============================================
# Example 1: Creating a REST Service Client
# ============================================


class PaymentGatewayClient(RESTService):
    """
    Example payment gateway REST API client.
    """

    async def create_payment(self, amount: float, currency: str) -> Dict[str, Any]:
        """Create a payment transaction."""
        return await self.post_json(
            "/payments",
            json={
                "amount": amount,
                "currency": currency,
            },
        )

    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Get payment status."""
        return await self.get_json(f"/payments/{payment_id}")

    async def refund_payment(self, payment_id: str) -> Dict[str, Any]:
        """Refund a payment."""
        return await self.post_json(f"/payments/{payment_id}/refund")


# Initialize the client (typically done in startup)
# create_rest_client(
#     name="payment_gateway",
#     base_url="https://api.payment-gateway.com",
#     api_key="your-api-key",
#     endpoint_base="/v1",
# )


# ============================================
# Example 2: Using REST Client in FastAPI Route
# ============================================


# Example API route using the REST client
async def create_payment_endpoint(
    amount: float,
    currency: str,
    payment_client: RESTService = Depends(get_rest_client("payment_gateway")),
) -> Dict[str, Any]:
    """
    Create a payment using the external payment gateway.

    Usage:
        POST /api/v1/payments/create
        {
            "amount": 100.00,
            "currency": "USD"
        }
    """
    result = await payment_client.create_payment(amount, currency)
    return {"payment_id": result["id"], "status": result["status"]}


# ============================================
# Example 3: Creating a WebSocket Service Client
# ============================================


class RealtimeDataService(WebSocketService):
    """
    Example WebSocket service for real-time data feeds.
    """

    def __init__(self):
        super().__init__(
            base_url="ws://realtime-data.example.com",
            endpoint="/stream",
            api_key="your-api-key",
        )
        self._received_messages = []

    async def on_connect(self):
        """Called when connection is established."""
        await self.send_json({"action": "subscribe", "channels": ["prices", "updates"]})

    async def on_disconnect(self):
        """Called when connection is closed."""
        print("Disconnected from real-time data service")

    async def on_message(self, message: str | bytes):
        """Called for each incoming message."""
        import json

        data = json.loads(message) if isinstance(message, str) else message
        self._received_messages.append(data)
        print(f"Received message: {data}")

    async def on_error(self, error: Exception):
        """Called when an error occurs."""
        print(f"WebSocket error: {error}")

    def get_latest_messages(self) -> list:
        """Get the latest received messages."""
        return self._received_messages


# ============================================
# Example 4: Using WebSocket Client
# ============================================


async def connect_to_realtime_service():
    """
    Example of connecting to and using a WebSocket service.
    """
    ws_client = RealtimeDataService()

    try:
        # Connect to the service
        await ws_client.connect()

        # Wait for some messages
        import asyncio

        await asyncio.sleep(10)

        # Get latest messages
        messages = ws_client.get_latest_messages()
        print(f"Received {len(messages)} messages")

        # Send a custom message
        await ws_client.send_json({"action": "get_status", "request_id": "12345"})

        # Check health
        is_healthy = await ws_client.health_check()
        print(f"Service healthy: {is_healthy}")

    finally:
        # Disconnect when done
        await ws_client.disconnect()


# ============================================
# Example 5: Background Task Integration
# ============================================


async def process_payment_notification(
    payment_id: str,
    payment_client: RESTService = Depends(get_rest_client("payment_gateway")),
):
    """
    Example background task to send notification after payment processing.

    Called after a payment is processed to notify external service.
    """
    try:
        await payment_client.post_json(
            "/notifications",
            json={
                "type": "payment_processed",
                "payment_id": payment_id,
                "timestamp": "2026-01-18T12:00:00Z",
            },
        )
    except Exception as e:
        print(f"Failed to send notification: {e}")


async def create_payment_with_notification(
    amount: float,
    currency: str,
    background_tasks: BackgroundTasks,
    payment_client: RESTService = Depends(get_rest_client("payment_gateway")),
) -> Dict[str, Any]:
    """
    Create payment and schedule background notification.
    """
    # Create payment
    result = await payment_client.create_payment(amount, currency)

    # Schedule background task for notification
    background_tasks.add_task(process_payment_notification, payment_id=result["id"])

    return {
        "payment_id": result["id"],
        "status": result["status"],
        "notification_scheduled": True,
    }


# ============================================
# Example 6: Custom REST Client with Authentication
# ============================================


class AuthenticatedRESTClient(RESTService):
    """
    REST client with custom authentication logic.
    """

    async def get_auth_headers(self) -> Dict[str, str]:
        """Get custom authentication headers."""
        # Example: OAuth token refresh logic
        access_token = await self._get_access_token()
        return {"Authorization": f"Bearer {access_token}", "X-API-Version": "v2"}

    async def _get_access_token(self) -> str:
        """Get or refresh access token."""
        # Implement your token refresh logic here
        return "your-access-token"

    async def get_authenticated(self, endpoint: str) -> Dict[str, Any]:
        """Make authenticated GET request."""
        headers = await self.get_auth_headers()
        return await self.get_json(endpoint, headers=headers)


# ============================================
# Example 7: Custom Message Handlers for WebSocket
# ============================================


class CustomWebSocketHandler:
    """Custom handler for specific message types."""

    async def handle_price_update(self, message: str | bytes):
        """Handle price update messages."""
        import json

        data = json.loads(message) if isinstance(message, str) else message
        if data.get("type") == "price_update":
            print(f"Price update: {data}")
            # Process price update...

    async def handle_alert(self, message: str | bytes):
        """Handle alert messages."""
        import json

        data = json.loads(message) if isinstance(message, str) else message
        if data.get("type") == "alert":
            print(f"Alert: {data}")
            # Handle alert...


async def setup_websocket_with_handlers():
    """
    Setup WebSocket client with custom message handlers.
    """
    ws_client = RealtimeDataService()
    handler = CustomWebSocketHandler()

    # Add custom handlers
    ws_client.add_message_handler(handler.handle_price_update)
    ws_client.add_message_handler(handler.handle_alert)

    try:
        await ws_client.connect()
        import asyncio

        await asyncio.sleep(60)
    finally:
        await ws_client.disconnect()
