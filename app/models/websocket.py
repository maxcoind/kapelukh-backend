from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel


class WSSubscription(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    subscription_id: str = Field(unique=True, index=True)
    username: str = Field(index=True)
    topic: str = Field(index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WSSubscriptionRow(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    subscription_id: str = Field(index=True)
    record_id: int = Field(index=True)
    row_index: int
    record_data: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
