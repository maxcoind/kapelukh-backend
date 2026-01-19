from datetime import datetime, timezone
from typing import Optional, Literal, Union, List
from pydantic import BaseModel, Field


class SubscriptionParams(BaseModel):
    """Simplified subscription params without filters."""

    event_types: List[Literal["created", "updated", "deleted"]] = Field(
        default_factory=lambda: ["created", "updated", "deleted"]
    )


class SubscribeMessage(BaseModel):
    type: Literal["subscribe"]
    topic: str
    params: SubscriptionParams = Field(default_factory=SubscriptionParams)


class UnsubscribeMessage(BaseModel):
    type: Literal["unsubscribe"]
    topic: str


class PingMessage(BaseModel):
    type: Literal["ping"]


ClientMessage = Union[SubscribeMessage, UnsubscribeMessage, PingMessage]


class ServerMessage(BaseModel):
    type: str
    topic: Optional[str] = None
    subscription_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data: Optional[dict] = None
    message: Optional[str] = None


class SubscribedData(BaseModel):
    """Generic subscribed data response."""

    items: list[dict]
    total: int


class EventData(BaseModel):
    """Event data sent to subscribers."""

    event_type: Literal["created", "updated", "deleted"]
    topic: str
    subscription_id: str
    record_data: dict
    timestamp: datetime
