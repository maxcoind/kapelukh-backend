# WebSocket Documentation

## Overview

The WebSocket API provides real-time notifications for model changes in the system. Clients can subscribe to specific topics and receive instant updates when records are created, updated, or deleted.

- **Protocol**: WebSocket
- **Connection URL**: Configurable (provided by your environment)
- **Authentication**: JWT access token via query parameter (required for subscriptions)

---

## Connection Details

### Endpoint

```
ws://your-server/ws
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token` | string | No | JWT access token (required for subscriptions) |

### Connection Behavior

- Connection is accepted immediately
- Invalid token allows connection but blocks subscription operations
- Unique client ID is automatically assigned to each connection
- Clients can remain connected without authentication but cannot subscribe

### Close Codes

| Code | Description |
|------|-------------|
| 1008 | Invalid token (token validation failed) |

---

## Client Messages

Clients send messages to the server in JSON format.

### Subscribe

Subscribe to receive real-time updates for a specific topic.

```json
{
  "type": "subscribe",
  "topic": "payment",
  "params": {
    "event_types": ["created", "updated", "deleted"]
  }
}
```

**Fields:**
- `type` (string): Must be `"subscribe"`
- `topic` (string): One of the available topics (see Available Topics section)
- `params.event_types` (array of strings): Event types to receive. Valid values: `"created"`, `"updated"`, `"deleted"`. Default: all types

### Unsubscribe

Stop receiving updates for a specific topic.

```json
{
  "type": "unsubscribe",
  "topic": "payment"
}
```

**Fields:**
- `type` (string): Must be `"unsubscribe"`
- `topic` (string): Topic to unsubscribe from

### Ping

Send a heartbeat to maintain the connection.

```json
{
  "type": "ping"
}
```

**Fields:**
- `type` (string): Must be `"ping"`

---

## Server Messages

The server sends messages to clients in JSON format.

### Subscribed

Confirmation of successful subscription with initial data.

```json
{
  "type": "subscribed",
  "topic": "payment",
  "subscription_id": "abc123xyz789",
  "timestamp": "2026-01-19T12:00:00Z",
  "data": {
    "items": [
      {
        "id": 1,
        "customer_id": 123,
        "amount": 100.50,
        "date": "2026-01-13T12:00:00Z"
      }
    ],
    "total": 100
  }
}
```

**Fields:**
- `type` (string): `"subscribed"`
- `topic` (string): Subscribed topic name
- `subscription_id` (string): Unique identifier for this subscription
- `timestamp` (string): ISO 8601 datetime
- `data.items` (array): Initial records (maximum 100)
- `data.total` (integer): Total count of records

### Unsubscribed

Confirmation of successful unsubscription.

```json
{
  "type": "unsubscribed",
  "topic": "payment",
  "subscription_id": "abc123xyz789",
  "timestamp": "2026-01-19T12:00:00Z"
}
```

**Fields:**
- `type` (string): `"unsubscribed"`
- `topic` (string): Unsubscribed topic name
- `subscription_id` (string): Identifier of the removed subscription
- `timestamp` (string): ISO 8601 datetime

### Event

Real-time notification of a model change.

```json
{
  "type": "event",
  "topic": "payment",
  "event_type": "created",
  "subscription_id": "abc123xyz789",
  "data": {
    "id": 2,
    "customer_id": 456,
    "amount": 250.00,
    "date": "2026-01-19T14:30:00Z"
  },
  "timestamp": "2026-01-19T14:30:00Z"
}
```

**Fields:**
- `type` (string): `"event"`
- `topic` (string): Topic that generated the event
- `event_type` (string): Event type: `"created"`, `"updated"`, or `"deleted"`
- `subscription_id` (string): Subscription receiving the event
- `data` (object): Record data (structure depends on topic)
- `timestamp` (string): ISO 8601 datetime when the event occurred

### Pong

Response to a ping message.

```json
{
  "type": "pong",
  "timestamp": "2026-01-19T12:00:00Z"
}
```

**Fields:**
- `type` (string): `"pong"`
- `timestamp` (string): ISO 8601 datetime

### Error

Error message when an operation fails.

```json
{
  "type": "error",
  "timestamp": "2026-01-19T12:00:00Z",
  "message": "Authentication required",
  "code": "AUTH_REQUIRED"
}
```

**Fields:**
- `type` (string): `"error"`
- `timestamp` (string): ISO 8601 datetime
- `message` (string): Human-readable error description
- `code` (string): Machine-readable error code (see Error Codes section)

---

## Available Topics

### payment

Events for the Payment model.

**Data Structure:**
```json
{
  "id": 1,
  "customer_id": 123,
  "amount": 100.50,
  "date": "2026-01-13T12:00:00Z"
}
```

**Fields:**
- `id` (integer): Payment ID
- `customer_id` (integer): Customer ID
- `amount` (number): Payment amount (decimal)
- `date` (string): ISO 8601 datetime

### telegram_user

Events for the TelegramUser model.

**Data Structure:**
```json
{
  "id": 1,
  "telegram_id": 123456789,
  "username": "john_doe",
  "first_name": "John",
  "last_name": "Doe",
  "language_code": "en",
  "is_active": true,
  "is_bot": false,
  "created_at": "2026-01-16T12:00:00Z",
  "updated_at": "2026-01-16T12:00:00Z",
  "last_interaction_at": "2026-01-16T14:30:00Z"
}
```

**Fields:**
- `id` (integer): Database ID
- `telegram_id` (integer): Telegram user ID
- `username` (string | null): Telegram username
- `first_name` (string): User's first name
- `last_name` (string | null): User's last name
- `language_code` (string | null): User's language code
- `is_active` (boolean): Active status
- `is_bot` (boolean): Bot status
- `created_at` (string): ISO 8601 datetime when record was created
- `updated_at` (string): ISO 8601 datetime when record was last updated
- `last_interaction_at` (string | null): ISO 8601 datetime of last interaction

### survey

Events for the Survey model.

**Data Structure:**
```json
{
  "id": 1,
  "user_id": 123456789,
  "full_name": {
    "first_name": "John",
    "last_name": "Doe"
  },
  "super_powers": ["coding", "leadership"],
  "birth_date": "1990-01-15",
  "traits_to_improve": ["patience", "public speaking"],
  "to_buy": ["laptop", "books"],
  "to_sell": ["old phone"],
  "service": "Consulting",
  "material_goal": "Buy a house",
  "social_goal": "Build a community",
  "spiritual_goal": "Find inner peace",
  "created_at": "2026-01-19T12:00:00Z",
  "updated_at": "2026-01-19T12:00:00Z"
}
```

**Fields:**
- `id` (integer): Database ID
- `user_id` (integer): Telegram user ID (unique)
- `full_name` (object): User's full name as key-value pairs
- `super_powers` (array): List of user's super powers
- `birth_date` (string): User's birth date
- `traits_to_improve` (array): List of traits user wants to improve
- `to_buy` (array): List of items user wants to buy
- `to_sell` (array): List of items user wants to sell
- `service` (string | null): Service description
- `material_goal` (string | null): Material goal
- `social_goal` (string | null): Social goal
- `spiritual_goal` (string | null): Spiritual goal
- `created_at` (string): ISO 8601 datetime when record was created
- `updated_at` (string): ISO 8601 datetime when record was last updated

---

## Subscription Parameters

### Limits

- **Maximum subscriptions per user**: 10
- **Initial data limit**: 100 records per subscription

### Event Types Filter

Clients can specify which event types to receive:

| Event Type | Description |
|------------|-------------|
| `created` | New record created via REST API POST |
| `updated` | Existing record modified via REST API PUT |
| `deleted` | Record deleted via REST API DELETE |

**Default Behavior**: If no `event_types` are specified, all event types are received.

**Example - Filter specific events:**
```json
{
  "type": "subscribe",
  "topic": "payment",
  "params": {
    "event_types": ["created", "updated"]
  }
}
```

---

## Error Codes

| Code | Description | When Triggered |
|------|-------------|----------------|
| `AUTH_REQUIRED` | Authentication required | Client attempts to subscribe without a valid JWT token |
| `MAX_SUBSCRIPTIONS` | Maximum subscriptions exceeded | Client exceeds limit of 10 active subscriptions |
| `INVALID_TOPIC` | Invalid topic | Client subscribes to a topic that is not registered |
| `INVALID_TYPE` | Invalid message type | Client sends a message with unknown `type` field |
| `INVALID_FORMAT` | Invalid message format | Client sends malformed JSON or missing required fields |
| `PLUGIN_NOT_FOUND` | Plugin not found | Topic handler is not available |

---

## Event Flow

1. **REST API Operation**: A record is created, updated, or deleted via REST API (POST/PUT/DELETE)
2. **Event Generation**: The change triggers an event with type `"created"`, `"updated"`, or `"deleted"`
3. **Event Broadcast**: The event processor broadcasts the event to all WebSocket clients subscribed to that topic
4. **Client Notification**: Each subscribed client receives an `event` message with the updated data
5. **Filtering**: Clients receive only the event types they specified in their subscription parameters

---

## Best Practices

### Authentication

- **Token renewal**: Renew JWT tokens before they expire (default access token expiry: 30 minutes)
- **Connection without auth**: You can establish connections without authentication, but you must provide a valid token to subscribe

### Connection Management

- **Reconnection**: Implement automatic reconnection logic to handle network interruptions
- **Graceful shutdown**: Properly close WebSocket connections when your application shuts down
- **Heartbeat**: Send `ping` messages periodically (e.g., every 30 seconds) to maintain connection and detect disconnections

### Subscription Management

- **Cleanup**: Unsubscribe from topics you no longer need to avoid hitting the subscription limit
- **Event filtering**: Specify only the event types you need to reduce bandwidth
- **Initial data**: Remember that subscriptions include initial data (up to 100 records)

### Error Handling

- **Parse error codes**: Handle errors gracefully based on the error code
- **Log errors**: Log error messages and codes for debugging
- **Recovery**: Implement recovery strategies for common error scenarios (e.g., authentication failures)

### Rate Limiting

- Respect WebSocket connection limits
- Avoid sending excessive `ping` messages
- Consider implementing client-side throttling for message processing

---

## Message Flow Example

1. **Client connects** with JWT token
2. **Server accepts** connection, assigns client ID
3. **Client subscribes** to `payment` topic with all event types
4. **Server confirms** subscription, sends initial 100 payments
5. **REST API** creates a new payment via POST `/api/v1/payments/`
6. **Server broadcasts** `event` message with event_type `"created"` to subscribed clients
7. **Client receives** event with new payment data
8. **Client unsubscribes** from `payment` topic
9. **Server confirms** unsubscription

---

## Notes

- WebSocket connections are persistent; manage connection lifecycle carefully
- Events are delivered in the order they occur
- Multiple clients can subscribe to the same topic
- Initial data is fetched when subscribing (up to 100 records)
- Events are broadcast to all clients subscribed to a topic
- Connection closes automatically on client disconnect or server shutdown
