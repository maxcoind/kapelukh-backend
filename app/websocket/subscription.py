from typing import List, Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.websocket import WSSubscription, WSSubscriptionRow
from app.crud.websocket import (
    create_subscription as crud_create_subscription,
    get_subscription_by_id,
    get_subscriptions_by_topic,
    get_subscriptions_by_username,
    delete_subscription as crud_delete_subscription,
    get_subscription_rows,
    delete_subscription_rows,
    create_subscription_row,
)


class SubscriptionManager:
    """Manager for WebSocket topic subscriptions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_subscription(self, username: str, topic: str) -> WSSubscription:
        """Create a new subscription for a user on a topic."""
        return await crud_create_subscription(
            session=self.db, username=username, topic=topic
        )

    async def delete_subscription(self, subscription_id: str) -> bool:
        """
        Delete a subscription and all its rows.
        Returns True if subscription was deleted, False if not found.
        """
        subscription = await get_subscription_by_id(
            session=self.db, subscription_id=subscription_id
        )
        if not subscription:
            return False

        # Delete all associated rows
        await delete_subscription_rows(session=self.db, subscription_id=subscription_id)

        # Delete the subscription
        await crud_delete_subscription(session=self.db, subscription_id=subscription_id)
        return True

    async def get_subscription(self, subscription_id: str) -> Optional[WSSubscription]:
        """Get a subscription by its ID."""
        return await get_subscription_by_id(
            session=self.db, subscription_id=subscription_id
        )

    async def get_subscriptions_by_topic(self, topic: str) -> List[WSSubscription]:
        """Get all subscriptions for a specific topic."""
        return await get_subscriptions_by_topic(session=self.db, topic=topic)

    async def get_user_subscriptions(self, username: str) -> List[WSSubscription]:
        """Get all subscriptions for a specific user."""
        return await get_subscriptions_by_username(session=self.db, username=username)

    async def update_subscription_rows(
        self, subscription_id: str, records_data: List[dict]
    ) -> None:
        """
        Replace all rows for a subscription with new record data.
        Used when initial subscription data is loaded.
        """
        # Delete existing rows
        await delete_subscription_rows(session=self.db, subscription_id=subscription_id)

        # Create new rows
        for index, record_data in enumerate(records_data):
            await create_subscription_row(
                session=self.db,
                subscription_id=subscription_id,
                record_id=record_data.get("id"),
                row_index=index,
                record_data=record_data,
            )

    async def get_subscription_rows(
        self, subscription_id: str
    ) -> List[WSSubscriptionRow]:
        """Get all rows for a subscription."""
        return await get_subscription_rows(
            session=self.db, subscription_id=subscription_id
        )
