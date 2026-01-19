from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.telegram_user import TelegramUser
from app.schemas.telegram_user import TelegramUserCreate, TelegramUserUpdate


async def create_telegram_user(
    db: AsyncSession, user_create: TelegramUserCreate
) -> TelegramUser:
    result = await db.execute(
        select(TelegramUser).where(
            getattr(TelegramUser, "telegram_id") == user_create.telegram_id
        )
    )
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Telegram user with ID {user_create.telegram_id} already exists",
        )

    db_user = TelegramUser.model_validate(user_create)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def get_telegram_user(
    db: AsyncSession, telegram_id: int
) -> Optional[TelegramUser]:
    result = await db.execute(
        select(TelegramUser).where(getattr(TelegramUser, "telegram_id") == telegram_id)
    )
    return result.scalar_one_or_none()


async def get_telegram_users(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    telegram_id: Optional[int] = None,
    username: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_bot: Optional[bool] = None,
    created_from: Optional[datetime] = None,
    created_to: Optional[datetime] = None,
    updated_from: Optional[datetime] = None,
    updated_to: Optional[datetime] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
) -> List[TelegramUser]:
    query = select(TelegramUser)

    if telegram_id is not None:
        query = query.where(getattr(TelegramUser, "telegram_id") == telegram_id)

    if username is not None and TelegramUser.username is not None:
        query = query.where(getattr(TelegramUser, "username").ilike(f"%{username}%"))

    if is_active is not None:
        query = query.where(getattr(TelegramUser, "is_active") == is_active)

    if is_bot is not None:
        query = query.where(getattr(TelegramUser, "is_bot") == is_bot)

    if created_from is not None:
        query = query.where(getattr(TelegramUser, "created_at") >= created_from)

    if created_to is not None:
        query = query.where(getattr(TelegramUser, "created_at") <= created_to)

    if updated_from is not None:
        query = query.where(getattr(TelegramUser, "updated_at") >= updated_from)

    if updated_to is not None:
        query = query.where(getattr(TelegramUser, "updated_at") <= updated_to)

    sort_field = _get_sort_field(sort_by)
    sort_direction = _get_sort_direction(sort_order)
    query = query.order_by(sort_direction(getattr(TelegramUser, sort_field)))

    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    return list(result.scalars().all())


async def update_telegram_user(
    db: AsyncSession, db_user: TelegramUser, user_update: TelegramUserUpdate
) -> TelegramUser:
    user_data = user_update.model_dump(exclude_unset=True)
    for field, value in user_data.items():
        setattr(db_user, field, value)

    db_user.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def soft_delete_telegram_user(
    db: AsyncSession, telegram_id: int
) -> Optional[TelegramUser]:
    db_user = await get_telegram_user(db, telegram_id)
    if db_user:
        db_user.is_active = False
        db_user.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(db_user)
    return db_user


async def update_last_interaction(
    db: AsyncSession, telegram_id: int
) -> Optional[TelegramUser]:
    db_user = await get_telegram_user(db, telegram_id)
    if db_user:
        db_user.last_interaction_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(db_user)
    return db_user


def _get_sort_field(sort_by: Optional[str]) -> str:
    sort_fields = {
        "telegram_id": "telegram_id",
        "username": "username",
        "created_at": "created_at",
        "updated_at": "updated_at",
        "last_interaction_at": "last_interaction_at",
    }
    if sort_by is None:
        return "created_at"
    return sort_fields.get(sort_by, "created_at")


def _get_sort_direction(sort_order: str):
    return desc if sort_order == "desc" else asc
