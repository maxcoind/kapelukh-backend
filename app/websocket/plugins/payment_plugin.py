from typing import Type
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.payment import Payment
from app.websocket.plugin_system import ModelPlugin
from app.schemas.websocket import SubscriptionParams


class PaymentPlugin(ModelPlugin):
    """Plugin for Payment model."""

    topic: str = "payment"
    model_class: Type[SQLModel] = Payment
    primary_key: str = "id"

    async def to_dict(self, instance: Payment) -> dict:
        """Convert payment instance to dictionary."""
        return {
            "id": instance.id,
            "customer_id": instance.customer_id,
            "amount": float(instance.amount),
            "date": instance.date.isoformat() if instance.date else None,
        }

    async def fetch_initial_data(
        self, session: AsyncSession, params: SubscriptionParams
    ) -> dict:
        """Fetch initial payments for subscription."""
        # Simple query without filtering
        query = select(Payment).order_by(Payment.date.desc()).limit(100)
        result = await session.execute(query)
        payments = result.scalars().all()

        return {
            "items": [await self.to_dict(p) for p in payments],
            "total": len(payments),
        }
