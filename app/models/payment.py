from decimal import Decimal
from typing import Optional
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel


class Payment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(index=True)
    amount: Decimal = Field(decimal_places=2, max_digits=10, gt=0)
    date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True
    )
