import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .api import payments_router
from .api.auth import router as auth_router
from .api.telegram_users import router as telegram_users_router
from .api.telegram_webhook import router as telegram_webhook_router
from .api.survey import router as survey_router
from .bot import (
    get_bot,
    get_dispatcher,
    handlers,
    setup_bot,
    setup_webhook,
    shutdown_bot,
)
from .bot.middleware import DBSessionMiddleware
from .config import settings
from .database import create_db_and_tables, get_engine
from .logger import get_logger, get_logging_config, setup_logging
from .services import initialize_services, shutdown_services
from .websocket.plugins import register_plugins
from .websocket.routes import router as ws_router

setup_logging(settings.LOG_LEVEL, settings.LOG_FORMAT, settings.LOG_FILE)
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown events."""
    logger.info("Initializing database models...")
    await create_db_and_tables(get_engine())
    logger.info("Database models initialized successfully")

    logger.info("Registering model plugins...")
    register_plugins()
    from .websocket.plugins import model_registry

    logger.info(f"Registered topics: {', '.join(model_registry.get_all_topics())}")

    logger.info("Initializing external service clients...")
    await initialize_services()
    logger.info("External service clients initialized")

    bot = None
    dispatcher = None
    use_webhook = False
    try:
        if settings.is_bot_enabled():
            logger.info("Initializing Telegram bot...")
            bot, dispatcher = await setup_bot(str(settings.TELEGRAM_BOT_TOKEN))
            dispatcher.update.middleware(DBSessionMiddleware())
            dispatcher.include_router(handlers.router)

            if settings.TELEGRAM_POLLING:
                logger.info("Starting Telegram bot polling...")
                asyncio.create_task(dispatcher.start_polling(bot, handle_signals=False))
                logger.info("Telegram bot polling started")
            else:
                use_webhook = True
                logger.info("Setting up Telegram webhook...")

                if not settings.DOMAIN:
                    logger.warning(
                        "DOMAIN is not set. Using localhost for webhook. "
                        "This will not work in production."
                    )
                    domain = "http://localhost:8000"
                else:
                    domain = settings.DOMAIN

                webhook_url = f"{domain}{settings.TELEGRAM_WEBHOOK_PATH}"
                logger.warning(
                    f"Webhook URL: {webhook_url}. "
                    "Ensure this URL is publicly accessible and uses HTTPS in production."
                )

                webhook_secret = await setup_webhook(
                    bot,
                    dispatcher,
                    webhook_url,
                    settings.TELEGRAM_WEBHOOK_SECRET,
                )

                settings.TELEGRAM_WEBHOOK_SECRET = webhook_secret
                logger.info(f"Webhook registered at {webhook_url}")
        else:
            logger.info("Telegram bot is disabled (no token configured)")

        yield

    finally:
        logger.info("Shutting down external service clients...")
        await shutdown_services()
        logger.info("External service clients shut down")

        logger.info("Stopping Telegram bot...")
        await shutdown_bot(use_webhook=use_webhook)
        logger.info("Telegram bot stopped")

        logger.info("Shutting down...")
        await get_engine().dispose()
        logger.info("Database engine disposed")


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(payments_router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(
    telegram_users_router, prefix="/api/v1/telegram-users", tags=["telegram-users"]
)
app.include_router(survey_router, prefix="/api/v1/surveys", tags=["surveys"])
app.include_router(telegram_webhook_router)
app.include_router(ws_router, prefix="/ws", tags=["websocket"])

origins = []

if settings.DOMAIN:
    origins.append(settings.DOMAIN)
else:
    origins.append("http://localhost:3000")
    origins.append("http://127.0.0.1:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows specific origins
    allow_credentials=True,  # Allows cookies to be included in requests
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, etc.)
    allow_headers=["*"],  # Allows all headers
)


@app.get("/health")
async def health_check():
    """Health check endpoint to verify application, database, and Telegram status."""
    health_status = {"status": "ok"}

    try:
        async with get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["database"] = "disconnected"
        health_status["status"] = "error"

    bot = get_bot()
    dispatcher = get_dispatcher()

    if not bot or not dispatcher:
        health_status["telegram"] = "disabled"
    else:
        try:
            await bot.get_me()
            health_status["telegram"] = "connected"
        except Exception as e:
            logger.error(f"Telegram health check failed: {e}")
            health_status["telegram"] = "disconnected"
            health_status["status"] = "error"

    return health_status


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        log_config=get_logging_config(
            settings.LOG_LEVEL, settings.LOG_FORMAT, settings.LOG_FILE
        ),
    )
