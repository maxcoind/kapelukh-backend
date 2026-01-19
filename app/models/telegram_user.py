from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


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
        default_factory=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_interaction_at: Optional[datetime] = Field(default=None, index=True)
