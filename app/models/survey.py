from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import BigInteger, JSON, Text
from sqlmodel import Column, DateTime, Field, SQLModel


class Survey(SQLModel, table=True):
    __tablename__ = "surveys"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(
        sa_column=Column(BigInteger, unique=True, index=True),
        description="Telegram ID пользователя",
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc),
    )

    full_name: Dict[str, str] = Field(default={}, sa_column=Column(JSON))
    super_powers: List[str] = Field(default=[], sa_column=Column(JSON))
    birth_date: str = Field(default="")
    traits_to_improve: List[str] = Field(default=[], sa_column=Column(JSON))
    to_buy: List[str] = Field(default=[], sa_column=Column(JSON))
    to_sell: List[str] = Field(default=[], sa_column=Column(JSON))
    service: Optional[str] = Field(default=None, sa_column=Column(Text))
    material_goal: Optional[str] = Field(default=None, sa_column=Column(Text))
    social_goal: Optional[str] = Field(default=None, sa_column=Column(Text))
    spiritual_goal: Optional[str] = Field(default=None, sa_column=Column(Text))
