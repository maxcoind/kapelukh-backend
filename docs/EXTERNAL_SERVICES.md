# External Service Integration

This directory contains abstract services for integrating with external web services using REST and WebSocket protocols.

## Architecture

The external service layer follows the **DI Client Pattern** with async support:

```
app/services/
├── __init__.py           # Public API exports
├── base.py              # Base abstract class with common functionality
├── rest_service.py      # REST API client abstract class
├── ws_service.py        # WebSocket client abstract class
├── registry.py         # Client registry for dependency injection
└── examples.py         # Usage examples
```

## Core Components

### 1. BaseExternalService (`base.py`)

Abstract base class providing common functionality:

- **Connection Management**: Async context manager support
- **HTTP Client**: Async httpx client with connection pooling
- **Retry Logic**: Automatic retry with exponential backoff
- **Timeout Handling**: Configurable timeout for all operations
- **Error Handling**: Custom exceptions for different error types
- **Logging**: Request/response logging
- **Health Checks**: Abstract `health_check()` method

**Custom Exceptions**:
- `ExternalServiceError`: Base exception
- `ServiceConnectionError`: Connection failures
- `ServiceTimeoutError`: Request timeouts
- `ServiceRateLimitError`: Rate limit exceeded (HTTP 429)
- `ServiceResponseError`: HTTP errors (4xx, 5xx)

### 2. RESTService (`rest_service.py`)

Abstract REST API client with common HTTP operations:

**Methods**:
- `get(endpoint, params, headers)`: GET request
- `post(endpoint, json, data, headers)`: POST request
- `put(endpoint, json, data, headers)`: PUT request
- `patch(endpoint, json, data, headers)`: PATCH request
- `delete(endpoint, params, headers)`: DELETE request
- `get_json(endpoint, params, headers)`: GET + parse JSON
- `post_json(endpoint, json, headers)`: POST + parse JSON

**Features**:
- Automatic retry logic (configurable)
- Status code validation (raises exception on 4xx/5xx)
- JSON serialization/deserialization
- Request/response logging
- Health check via `/health` endpoint

### 3. WebSocketService (`ws_service.py`)

Abstract WebSocket client with connection management:

**Abstract Methods** (must implement):
- `on_connect()`: Called when connection established
- `on_disconnect()`: Called when connection closed
- `on_message(message)`: Called for each incoming message

**Methods**:
- `connect()`: Establish connection with auto-reconnect
- `disconnect()`: Close connection gracefully
- `send(message)`: Send text, bytes, or dict (JSON)
- `send_json(data)`: Send JSON data
- `add_message_handler(handler)`: Add custom message handler
- `remove_message_handler(handler)`: Remove message handler
- `health_check()`: Check connection health

**Features**:
- Automatic reconnection on disconnect
- Connection health monitoring
- Ping/pong keepalive
- Multiple message handlers support
- Graceful shutdown
- Custom error handling via `on_error()`

### 4. ServiceRegistry (`registry.py`)

Registry for managing and injecting service clients:

**Functions**:
- `create_rest_client(name, base_url, ...)`: Create and register REST client
- `create_ws_client(name, base_url, ...)`: Create and register WS client
- `get_service_client(name)`: Get any registered client
- `get_rest_client(name)`: Get REST client (type-safe)
- `get_ws_client(name)`: Get WS client (type-safe)
- `initialize_services()`: Initialize all clients from config
- `shutdown_services()`: Close all connections

## Usage Examples

### Creating a REST Service Client

```python
from app.services import RESTService, create_rest_client, get_rest_client
from fastapi import Depends

# Define your custom REST client
class PaymentGatewayClient(RESTService):
    async def create_payment(self, amount: float, currency: str):
        return await self.post_json(
            "/payments",
            json={"amount": amount, "currency": currency}
        )

# Initialize (typically in app startup)
create_rest_client(
    name="payment_gateway",
    base_url="https://api.payment-gateway.com",
    api_key="your-api-key",
    endpoint_base="/v1",
)

# Use in FastAPI route
@router.post("/payments")
async def create_payment(
    amount: float,
    client: RESTService = Depends(get_rest_client("payment_gateway"))
):
    result = await client.create_payment(amount, "USD")
    return result
```

### Creating a WebSocket Service Client

```python
from app.services import WebSocketService
import asyncio

class RealtimeDataService(WebSocketService):
    def __init__(self):
        super().__init__(
            base_url="ws://realtime.example.com",
            endpoint="/stream",
            api_key="your-api-key",
        )
        self._messages = []

    async def on_connect(self):
        # Subscribe to channels after connecting
        await self.send_json({
            "action": "subscribe",
            "channels": ["prices", "updates"]
        })

    async def on_disconnect(self):
        print("Disconnected")

    async def on_message(self, message):
        import json
        data = json.loads(message)
        self._messages.append(data)

# Use the client
async def main():
    ws_client = RealtimeDataService()
    try:
        await ws_client.connect()
        await asyncio.sleep(30)  # Run for 30 seconds
        messages = ws_client._messages
        print(f"Received {len(messages)} messages")
    finally:
        await ws_client.disconnect()
```

### Using with Background Tasks

```python
from fastapi import BackgroundTasks

async def send_notification(
    payment_id: str,
    client: RESTService = Depends(get_rest_client("notification_service"))
):
    await client.post_json(
        "/notify",
        json={"payment_id": payment_id}
    )

@router.post("/payments")
async def create_payment(
    amount: float,
    background_tasks: BackgroundTasks,
    client: RESTService = Depends(get_rest_client("payment_gateway"))
):
    # Create payment
    result = await client.create_payment(amount, "USD")
    
    # Schedule background notification
    background_tasks.add_task(
        send_notification,
        payment_id=result["id"]
    )
    
    return result
```

### Custom Message Handlers

```python
class CustomHandler:
    async def handle_alert(self, message):
        data = json.loads(message)
        if data.get("type") == "alert":
            # Handle alert...
            pass

ws_client = RealtimeDataService()
handler = CustomHandler()
ws_client.add_message_handler(handler.handle_alert)
```

## Configuration

### Adding External Service Settings

Add to `app/config.py`:

```python
class Settings(BaseSettings):
    # External API settings
    PAYMENT_GATEWAY_URL: str = "https://api.payment-gateway.com"
    PAYMENT_GATEWAY_API_KEY: str | None = None
    PAYMENT_GATEWAY_TIMEOUT: float = 30.0
    
    # WebSocket settings
    REALTIME_WS_URL: str = "ws://realtime.example.com"
    REALTIME_WS_KEY: str | None = None
    REALTIME_WS_PING_INTERVAL: float = 20.0
```

### Initializing Services

In `app/main.py`, add to lifespan:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... existing startup code ...
    
    logger.info("Initializing external service clients...")
    await initialize_services()
    logger.info("External service clients initialized")
    
    try:
        yield
    finally:
        logger.info("Shutting down external service clients...")
        await shutdown_services()
        logger.info("External service clients shut down")
        
        # ... existing shutdown code ...
```

In `app/services/registry.py`, update `initialize_services()`:

```python
async def initialize_services():
    logger.info("Initializing service clients...")
    
    if settings.PAYMENT_GATEWAY_URL:
        create_rest_client(
            name="payment_gateway",
            base_url=settings.PAYMENT_GATEWAY_URL,
            api_key=settings.PAYMENT_GATEWAY_API_KEY,
            timeout=settings.PAYMENT_GATEWAY_TIMEOUT,
        )
    
    if settings.REALTIME_WS_URL:
        create_ws_client(
            name="realtime_ws",
            base_url=settings.REALTIME_WS_URL,
            api_key=settings.REALTIME_WS_KEY,
            ping_interval=settings.REALTIME_WS_PING_INTERVAL,
        )
    
    logger.info(f"Initialized {len(ServiceRegistry._clients)} service clients")
```

## Best Practices

1. **Use Async Context Managers**: Always use `async with` for WebSocket clients
2. **Handle Exceptions**: Catch and handle service-specific exceptions
3. **Configure Timeouts**: Set appropriate timeouts for your services
4. **Use Background Tasks**: Offload slow external calls to background tasks
5. **Log Errors**: All errors are logged automatically
6. **Test Locally**: Mock external services in tests using dependency injection
7. **Rate Limiting**: Implement rate limiting if API has limits
8. **Health Checks**: Call `health_check()` before critical operations

## Testing

### Mocking Services

```python
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

def test_payment_creation():
    # Mock the client
    mock_client = AsyncMock()
    mock_client.create_payment = AsyncMock(
        return_value={"id": "123", "status": "created"}
    )
    
    # Override dependency
    app.dependency_overrides[get_rest_client] = lambda: mock_client
    
    # Test
    client = TestClient(app)
    response = client.post("/api/v1/payments", json={"amount": 100.00})
    assert response.status_code == 200
```

## Dependencies

Added to `pyproject.toml`:
- `websockets>=14.0.0`: WebSocket client library
- `tenacity>=8.2.0`: Retry logic with exponential backoff
- `httpx>=0.28.1`: Async HTTP client (already present)

## Files Created

1. `app/services/base.py` - Base service class
2. `app/services/rest_service.py` - REST client
3. `app/services/ws_service.py` - WebSocket client
4. `app/services/registry.py` - Client registry
5. `app/services/__init__.py` - Public API
6. `app/services/examples.py` - Usage examples

## Next Steps

1. Add configuration for your external services in `app/config.py`
2. Implement concrete client classes by extending `RESTService` or `WebSocketService`
3. Register clients in `initialize_services()` in `registry.py`
4. Use `get_rest_client()` or `get_ws_client()` dependencies in your API routes
5. Add tests with mocked clients
