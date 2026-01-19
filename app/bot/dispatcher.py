import asyncio
import secrets
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import WebhookInfo

_bot: Optional[Bot] = None
_dispatcher: Optional[Dispatcher] = None
_webhook_secret: Optional[str] = None


async def setup_bot(token: str) -> tuple[Bot, Dispatcher]:
    """Initialize bot and dispatcher."""
    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = Dispatcher()

    global _bot, _dispatcher
    _bot = bot
    _dispatcher = dispatcher

    return bot, dispatcher


async def setup_webhook(
    bot: Bot,
    dispatcher: Dispatcher,
    webhook_url: str,
    secret_token: Optional[str] = None,
) -> str:
    """Setup webhook for the bot.

    Args:
        bot: Bot instance
        dispatcher: Dispatcher instance
        webhook_url: Full URL for webhook endpoint
        secret_token: Optional secret token for webhook verification

    Returns:
        The secret token used (generated if not provided)
    """
    global _webhook_secret

    if secret_token is None:
        secret_token = secrets.token_hex(32)
    _webhook_secret = secret_token

    await bot.set_webhook(url=webhook_url, secret_token=secret_token)
    return secret_token


async def get_webhook_info(bot: Bot) -> WebhookInfo:
    """Get current webhook information.

    Args:
        bot: Bot instance

    Returns:
        WebhookInfo object with current webhook status
    """
    return await bot.get_webhook_info()


async def shutdown_bot(timeout: float = 5.0, use_webhook: bool = False):
    """Gracefully shutdown the bot.

    Args:
        timeout: Maximum time to wait for graceful shutdown in seconds.
        use_webhook: Whether the bot is running in webhook mode.
    """
    if _dispatcher:
        await _dispatcher.stop_polling()

    if _bot:
        if use_webhook:
            await _bot.delete_webhook()

        try:
            await asyncio.wait_for(_bot.session.close(), timeout=timeout)
        except asyncio.TimeoutError:
            pass
        except (asyncio.CancelledError, Exception):
            pass


def get_bot() -> Optional[Bot]:
    """Get bot instance."""
    return _bot


def get_dispatcher() -> Optional[Dispatcher]:
    """Get dispatcher instance."""
    return _dispatcher


def get_webhook_secret() -> Optional[str]:
    """Get webhook secret token."""
    return _webhook_secret
