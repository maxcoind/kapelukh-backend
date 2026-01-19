from datetime import datetime
from typing import List, Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from app.auth import get_current_user
from app.crud.telegram_user import (
    create_telegram_user,
    get_telegram_user,
    get_telegram_users,
    soft_delete_telegram_user,
    update_last_interaction,
    update_telegram_user,
)
from app.database import getDbSession
from app.models.telegram_user import TelegramUser
from app.schemas.telegram_user import (
    TelegramUserCreate,
    TelegramUserRead,
    TelegramUserUpdate,
)
from app.websocket.integration import ModelEventHelper
from app.websocket.plugins.telegram_user_plugin import TelegramUserPlugin
from app.websocket.routes import get_connection_manager

router = APIRouter()


async def trigger_user_event(
    user: TelegramUser, event_type: Literal["created", "updated", "deleted"], session
):
    """Trigger telegram user event via EventProcessor."""
    connection_manager = get_connection_manager()

    plugin = TelegramUserPlugin()
    await ModelEventHelper.trigger_event(
        db=session,
        connection_manager=connection_manager,
        topic="telegram_user",
        event_type=event_type,
        instance=user,
        to_dict_func=plugin.to_dict,
    )


@router.post("/", response_model=TelegramUserRead, status_code=status.HTTP_201_CREATED)
async def create(
    *,
    session=Depends(getDbSession),
    user_create: TelegramUserCreate,
    current_user: str = Depends(get_current_user),
    background_tasks: BackgroundTasks,
) -> TelegramUser:
    user = await create_telegram_user(session, user_create)
    background_tasks.add_task(trigger_user_event, user, "created", session)
    return user


@router.get("/{telegram_id}", response_model=TelegramUserRead)
async def read(
    *,
    session=Depends(getDbSession),
    telegram_id: int,
    current_user: str = Depends(get_current_user),
) -> TelegramUser:
    user = await get_telegram_user(session, telegram_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Telegram user not found"
        )
    return user


@router.get("/", response_model=List[TelegramUserRead])
async def read_many(
    *,
    session=Depends(getDbSession),
    skip: int = 0,
    limit: int = 100,
    telegram_id: Optional[int] = Query(None),
    username: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_bot: Optional[bool] = Query(None),
    created_from: Optional[datetime] = Query(None),
    created_to: Optional[datetime] = Query(None),
    updated_from: Optional[datetime] = Query(None),
    updated_to: Optional[datetime] = Query(None),
    sort_by: Optional[str] = Query(
        None,
        description="Field to sort by (telegram_id, username, created_at, updated_at, last_interaction_at)",
    ),
    sort_order: Optional[str] = Query("desc", description="Sort order (asc, desc)"),
    current_user: str = Depends(get_current_user),
) -> List[TelegramUser]:
    return await get_telegram_users(
        session=session,
        skip=skip,
        limit=limit,
        telegram_id=telegram_id,
        username=username,
        is_active=is_active,
        is_bot=is_bot,
        created_from=created_from,
        created_to=created_to,
        updated_from=updated_from,
        updated_to=updated_to,
        sort_by=sort_by,
        sort_order=sort_order or "asc",
    )


@router.put("/{telegram_id}", response_model=TelegramUserRead)
async def update(
    *,
    session=Depends(getDbSession),
    telegram_id: int,
    user_update: TelegramUserUpdate,
    current_user: str = Depends(get_current_user),
    background_tasks: BackgroundTasks,
) -> TelegramUser:
    db_user = await get_telegram_user(session, telegram_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Telegram user not found"
        )
    user = await update_telegram_user(session, db_user, user_update)
    background_tasks.add_task(trigger_user_event, user, "updated", session)
    return user


@router.delete("/{telegram_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    *,
    session=Depends(getDbSession),
    telegram_id: int,
    current_user: str = Depends(get_current_user),
    background_tasks: BackgroundTasks,
) -> None:
    user = await get_telegram_user(session, telegram_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Telegram user not found"
        )
    await soft_delete_telegram_user(session, telegram_id)
    background_tasks.add_task(trigger_user_event, user, "deleted", session)


@router.patch("/{telegram_id}/last-interaction", response_model=TelegramUserRead)
async def update_interaction(
    *,
    session=Depends(getDbSession),
    telegram_id: int,
    current_user: str = Depends(get_current_user),
    background_tasks: BackgroundTasks,
) -> TelegramUser:
    user = await update_last_interaction(session, telegram_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Telegram user not found"
        )
    background_tasks.add_task(trigger_user_event, user, "updated", session)
    return user
