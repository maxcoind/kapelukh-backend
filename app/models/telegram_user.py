from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Column, DateTime, Field, SQLModel


class TelegramUser(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_id: int = Field(unique=True, index=True)
    username: Optional[str] = Field(default=None, max_length=32, index=True)
    first_name: str = Field(max_length=64)
    last_name: Optional[str] = Field(default=None, max_length=64)
    language_code: Optional[str] = Field(default=None, max_length=10)
    is_active: bool = Field(default=True, index=True)
    is_bot: bool = Field(default=False)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    last_interaction_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), index=True), default=None
    )
