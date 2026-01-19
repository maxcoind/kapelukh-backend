from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TelegramUserBase(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None
    language_code: Optional[str] = None
    is_active: bool = True
    is_bot: bool = False


class TelegramUserCreate(TelegramUserBase):
    telegram_id: int = Field(gt=0, description="Telegram user ID must be positive")


class TelegramUserUpdate(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None
    is_active: Optional[bool] = None
    is_bot: Optional[bool] = None


class TelegramUserRead(TelegramUserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    last_interaction_at: Optional[datetime] = None
