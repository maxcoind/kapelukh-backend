from typing import Optional

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_token
from app.database import getDbSession
from app.logger import get_logger
from app.schemas.websocket import (
    SubscribeMessage,
    UnsubscribeMessage,
)
from app.websocket.manager import ConnectionManager, SubscriptionState
from app.websocket.plugin_system import model_registry
from app.websocket.subscription import SubscriptionManager

logger = get_logger("ws.router")

router = APIRouter()

connection_manager = ConnectionManager()

MAX_SUBSCRIPTIONS_PER_USER = 10


def get_connection_manager():
    return connection_manager


@router.websocket("")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(default=None),
    db: AsyncSession = Depends(getDbSession),
):
    username: Optional[str] = None
    logger.info("client connected")
    if token:
        try:
            token_data = verify_token(token, "access")
            username = token_data.username
        except Exception:
            await websocket.close(code=1008, reason="Invalid token")
            return

    client_id = connection_manager.generate_client_id()
    await connection_manager.connect(client_id, websocket, username)

    try:
        while True:
            data = await websocket.receive_text()

            try:
                import json

                message = json.loads(data)

                msg_type = message.get("type")

                if msg_type == "subscribe":
                    client_message = SubscribeMessage(**message)
                    await handle_subscribe(client_id, username, client_message, db)
                elif msg_type == "unsubscribe":
                    client_message = UnsubscribeMessage(**message)
                    await handle_unsubscribe(client_id, client_message, db)
                elif msg_type == "ping":
                    pong_message = {"type": "pong", "timestamp": "2026-01-16T12:00:00Z"}
                    await connection_manager.send_message(client_id, pong_message)
                else:
                    error_message = {
                        "type": "error",
                        "timestamp": "2026-01-16T12:00:00Z",
                        "message": "Invalid message type",
                        "code": "INVALID_TYPE",
                    }
                    await connection_manager.send_message(client_id, error_message)
            except Exception:
                error_message = {
                    "type": "error",
                    "timestamp": "2026-01-16T12:00:00Z",
                    "message": "Invalid message format",
                    "code": "INVALID_FORMAT",
                }
                await connection_manager.send_message(client_id, error_message)

    except WebSocketDisconnect:
        await connection_manager.disconnect(client_id)


async def handle_subscribe(
    client_id: str, username: Optional[str], message: SubscribeMessage, db: AsyncSession
):
    from datetime import datetime, timezone

    if not username:
        error_message = {
            "type": "error",
            "timestamp": "2026-01-16T12:00:00Z",
            "message": "Authentication required",
            "code": "AUTH_REQUIRED",
        }
        await connection_manager.send_message(client_id, error_message)
        return

    session = connection_manager.get_client_session(client_id)
    if not session:
        return

    if len(session.subscriptions) >= MAX_SUBSCRIPTIONS_PER_USER:
        error_message = {
            "type": "error",
            "timestamp": "2026-01-16T12:00:00Z",
            "message": f"Maximum {MAX_SUBSCRIPTIONS_PER_USER} subscriptions allowed",
            "code": "MAX_SUBSCRIPTIONS",
        }
        await connection_manager.send_message(client_id, error_message)
        return

    # Validate topic
    if not model_registry.is_valid_topic(message.topic):
        valid_topics = model_registry.get_all_topics()
        error_message = {
            "type": "error",
            "timestamp": "2026-01-16T12:00:00Z",
            "message": f"Invalid topic. Valid topics: {', '.join(valid_topics)}",
            "code": "INVALID_TOPIC",
        }
        await connection_manager.send_message(client_id, error_message)
        return

    # Create subscription
    sub_manager = SubscriptionManager(db)
    subscription = await sub_manager.create_subscription(
        username=username, topic=message.topic
    )

    subscription_state = SubscriptionState(
        subscription_id=subscription.subscription_id,
        topic=message.topic,
        params=message.params,
    )

    connection_manager.add_subscription(client_id, subscription_state)

    # Fetch initial data using plugin
    plugin = model_registry.get(message.topic)
    if plugin:
        initial_data = await plugin.fetch_initial_data(db, message.params)

        subscribed_message = {
            "type": "subscribed",
            "topic": message.topic,
            "subscription_id": subscription.subscription_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": initial_data,
        }

        await connection_manager.send_message(client_id, subscribed_message)
    else:
        error_message = {
            "type": "error",
            "timestamp": "2026-01-16T12:00:00Z",
            "message": f"Plugin not found for topic: {message.topic}",
            "code": "PLUGIN_NOT_FOUND",
        }
        await connection_manager.send_message(client_id, error_message)


async def handle_unsubscribe(
    client_id: str, message: UnsubscribeMessage, db: AsyncSession
):
    session = connection_manager.get_client_session(client_id)
    if not session:
        return

    subscription_to_remove = None
    for sub_id, sub_state in session.subscriptions.items():
        if sub_state.topic == message.topic:
            subscription_to_remove = sub_id
            break

    if subscription_to_remove:
        connection_manager.remove_subscription(client_id, subscription_to_remove)

        sub_manager = SubscriptionManager(db)
        await sub_manager.delete_subscription(subscription_to_remove)

        unsubscribed_message = {
            "type": "unsubscribed",
            "topic": message.topic,
            "subscription_id": subscription_to_remove,
            "timestamp": "2026-01-16T12:00:00Z",
        }

        await connection_manager.send_message(client_id, unsubscribed_message)
