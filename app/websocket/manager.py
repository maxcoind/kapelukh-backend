import uuid
from datetime import datetime, timezone
from typing import Optional, Dict
from fastapi import WebSocket

from app.schemas.websocket import SubscriptionParams


class SubscriptionState:
    def __init__(self, subscription_id: str, topic: str, params: SubscriptionParams):
        self.subscription_id = subscription_id
        self.topic = topic
        self.params = params


class ClientSession:
    def __init__(self, client_id: str, username: Optional[str]):
        self.client_id = client_id
        self.username = username
        self.connected_at = datetime.now(timezone.utc)
        self.subscriptions: Dict[str, SubscriptionState] = {}


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_sessions: Dict[str, ClientSession] = {}

    async def connect(
        self, client_id: str, websocket: WebSocket, username: Optional[str] = None
    ) -> ClientSession:
        await websocket.accept()

        self.active_connections[client_id] = websocket
        session = ClientSession(client_id, username)
        self.client_sessions[client_id] = session

        return session

    async def disconnect(self, client_id: str) -> None:
        if client_id in self.active_connections:
            del self.active_connections[client_id]

        if client_id in self.client_sessions:
            del self.client_sessions[client_id]

    async def send_message(self, client_id: str, message: dict) -> bool:
        websocket = self.active_connections.get(client_id)
        if not websocket:
            return False

        try:

            await websocket.send_json(message)
            return True
        except Exception:
            return False

    async def broadcast_to_subscription(
        self, client_id: str, subscription_id: str, message: dict
    ) -> None:
        if client_id not in self.active_connections:
            return

        await self.send_message(client_id, message)

    def get_client_session(self, client_id: str) -> Optional[ClientSession]:
        return self.client_sessions.get(client_id)

    def add_subscription(self, client_id: str, subscription: SubscriptionState) -> None:
        session = self.get_client_session(client_id)
        if session:
            session.subscriptions[subscription.subscription_id] = subscription

    def remove_subscription(self, client_id: str, subscription_id: str) -> None:
        session = self.get_client_session(client_id)
        if session and subscription_id in session.subscriptions:
            del session.subscriptions[subscription_id]

    def get_subscription(
        self, client_id: str, subscription_id: str
    ) -> Optional[SubscriptionState]:
        session = self.get_client_session(client_id)
        if session:
            return session.subscriptions.get(subscription_id)
        return None

    def is_connected(self, client_id: str) -> bool:
        return client_id in self.active_connections

    def generate_client_id(self) -> str:
        return f"client_{uuid.uuid4().hex[:12]}"
