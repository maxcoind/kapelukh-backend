from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlmodel import and_, asc, desc, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentUpdate


class SortField(str, Enum):
    customer_id = "customer_id"
    amount = "amount"
    date = "date"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


async def create(*, session: AsyncSession, payment_create: PaymentCreate) -> Payment:
    db_obj = Payment.model_validate(payment_create)
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


async def get(*, session: AsyncSession, payment_id: int) -> Optional[Payment]:
    return await session.get(Payment, payment_id)


async def get_multi(
    *,
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    customer_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    sort_by: Optional[SortField] = None,
    sort_order: Optional[SortOrder] = None,
) -> List[Payment]:
    statement = select(Payment)
    conditions = []

    if customer_id is not None:
        conditions.append(Payment.customer_id == customer_id)

    if date_from is not None:
        conditions.append(Payment.date >= date_from)

    if date_to is not None:
        conditions.append(Payment.date <= date_to)

    if conditions:
        statement = statement.where(and_(*conditions))

    if sort_by:
        sort_column = getattr(Payment, sort_by.value)
        if sort_order == SortOrder.desc:
            statement = statement.order_by(desc(sort_column))
        else:
            statement = statement.order_by(asc(sort_column))

    statement = statement.offset(skip).limit(limit)
    result = await session.exec(statement)
    return list(result.all())


async def update(
    *, session: AsyncSession, db_obj: Payment, obj_in: PaymentUpdate
) -> Payment:
    obj_data = obj_in.model_dump(exclude_unset=True)
    for field, value in obj_data.items():
        setattr(db_obj, field, value)
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


async def remove(*, session: AsyncSession, payment_id: int) -> Optional[Payment]:
    obj = await session.get(Payment, payment_id)
    if obj:
        await session.delete(obj)
        await session.commit()
    return obj
