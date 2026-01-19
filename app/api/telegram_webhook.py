from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import get_bot, get_dispatcher, get_webhook_info, get_webhook_secret
from app.database import getDbSession

router = APIRouter()


@router.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(
        None, alias="X-Telegram-Bot-Api-Secret-Token"
    ),
    session: AsyncSession = Depends(getDbSession),
):
    """Handle Telegram webhook updates.

    Verifies the secret token from Telegram and processes the update through the dispatcher.
    """
    secret_token = get_webhook_secret()

    if not secret_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook not configured",
        )

    if x_telegram_bot_api_secret_token != secret_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid secret token",
        )

    bot = get_bot()
    dispatcher = get_dispatcher()

    if not bot or not dispatcher:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Bot not initialized",
        )

    update_data = await request.json()
    await dispatcher.feed_raw_update(bot=bot, update=update_data, session=session)

    return Response(status_code=status.HTTP_200_OK)


@router.get("/telegram/webhook/status")
async def webhook_status():
    """Get webhook status information."""
    bot = get_bot()
    dispatcher = get_dispatcher()

    if not bot or not dispatcher:
        return {
            "mode": "disabled",
            "url": None,
            "registered": False,
            "error": "Bot not initialized",
        }

    webhook_info = await get_webhook_info(bot)

    mode: Literal["webhook", "polling"]
    if webhook_info.url:
        mode = "webhook"
    else:
        mode = "polling"

    return {
        "mode": mode,
        "url": webhook_info.url,
        "registered": bool(webhook_info.url),
        "has_custom_certificate": webhook_info.has_custom_certificate,
        "pending_update_count": webhook_info.pending_update_count,
    }


webhook_status.__name__ = "webhook_status"
