import uuid
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.websocket import WSSubscription, WSSubscriptionRow


async def create_subscription(
    *, session: AsyncSession, username: str, topic: str
) -> WSSubscription:
    """Create a new subscription with UUID subscription_id."""
    subscription_id = f"sub_{uuid.uuid4().hex[:12]}"

    db_subscription = WSSubscription(
        subscription_id=subscription_id,
        username=username,
        topic=topic,
    )
    session.add(db_subscription)
    await session.commit()
    await session.refresh(db_subscription)
    return db_subscription


async def get_subscription_by_id(
    *, session: AsyncSession, subscription_id: str
) -> Optional[WSSubscription]:
    """Get subscription by subscription_id."""
    result = await session.execute(
        select(WSSubscription).where(WSSubscription.subscription_id == subscription_id)
    )
    return result.scalar_one_or_none()


async def get_subscriptions_by_topic(
    *, session: AsyncSession, topic: str
) -> List[WSSubscription]:
    """Get all subscriptions for a specific topic."""
    result = await session.execute(
        select(WSSubscription).where(WSSubscription.topic == topic)
    )
    return list(result.scalars().all())


async def get_subscriptions_by_username(
    *, session: AsyncSession, username: str
) -> List[WSSubscription]:
    """Get all subscriptions for a specific user."""
    result = await session.execute(
        select(WSSubscription).where(WSSubscription.username == username)
    )
    return list(result.scalars().all())


async def delete_subscription(
    *, session: AsyncSession, subscription_id: str
) -> Optional[WSSubscription]:
    """Delete subscription by subscription_id."""
    subscription = await get_subscription_by_id(
        session=session, subscription_id=subscription_id
    )
    if subscription:
        await session.execute(
            delete(WSSubscription).where(
                WSSubscription.subscription_id == subscription_id
            )
        )
        await session.commit()
    return subscription


async def update_subscription(
    *, session: AsyncSession, subscription_id: str
) -> Optional[WSSubscription]:
    """Update subscription timestamp."""
    subscription = await get_subscription_by_id(
        session=session, subscription_id=subscription_id
    )
    if subscription:
        subscription.updated_at = datetime.now(timezone.utc)
        session.add(subscription)
        await session.commit()
        await session.refresh(subscription)
    return subscription


async def create_subscription_row(
    *,
    session: AsyncSession,
    subscription_id: str,
    record_id: int,
    row_index: int,
    record_data: dict,
) -> WSSubscriptionRow:
    """Create a subscription row entry."""
    import json

    record_data_json = json.dumps(record_data)

    db_row = WSSubscriptionRow(
        subscription_id=subscription_id,
        record_id=record_id,
        row_index=row_index,
        record_data=record_data_json,
    )
    session.add(db_row)
    await session.commit()
    await session.refresh(db_row)
    return db_row


async def get_subscription_rows(
    *, session: AsyncSession, subscription_id: str
) -> List[WSSubscriptionRow]:
    """Get all rows for a subscription."""
    result = await session.execute(
        select(WSSubscriptionRow)
        .where(WSSubscriptionRow.subscription_id == subscription_id)
        .order_by(WSSubscriptionRow.row_index)
    )
    return list(result.scalars().all())


async def delete_subscription_rows(
    *, session: AsyncSession, subscription_id: str
) -> int:
    """Delete all rows for a subscription. Returns count of deleted rows."""
    stmt = delete(WSSubscriptionRow).where(
        WSSubscriptionRow.subscription_id == subscription_id
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount


async def get_subscription_row_by_record_id(
    *, session: AsyncSession, subscription_id: str, record_id: int
) -> Optional[WSSubscriptionRow]:
    """Find a row by record_id within a subscription."""
    result = await session.execute(
        select(WSSubscriptionRow).where(
            WSSubscriptionRow.subscription_id == subscription_id,
            WSSubscriptionRow.record_id == record_id,
        )
    )
    return result.scalar_one_or_none()


async def delete_subscription_row_by_record_id(
    *, session: AsyncSession, subscription_id: str, record_id: int
) -> bool:
    """Delete a row by record_id within a subscription."""
    row = await get_subscription_row_by_record_id(
        session=session, subscription_id=subscription_id, record_id=record_id
    )
    if row:
        await session.delete(row)
        await session.commit()
        return True
    return False
