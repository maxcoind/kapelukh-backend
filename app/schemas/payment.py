from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SortField(str, Enum):
    customer_id = "customer_id"
    amount = "amount"
    date = "date"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class PaymentBase(BaseModel):
    customer_id: int
    amount: Decimal = Field(decimal_places=2, max_digits=10, gt=0)
    date: datetime


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    customer_id: Optional[int] = None
    amount: Optional[Decimal] = Field(None, decimal_places=2, max_digits=10, gt=0)
    date: Optional[datetime] = None


class PaymentRead(PaymentBase):
    id: int
    customer_id: int

    model_config = ConfigDict(from_attributes=True)
