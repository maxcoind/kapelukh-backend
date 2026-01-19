from typing import Literal

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DbSettings(BaseModel):
    url: str = Field(
        default="sqlite+aiosqlite:///:memory:", description="SqlLite connection URL"
    )


class Settings(BaseSettings):
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="DEBUG")
    LOG_FORMAT: Literal["json", "text", "colored"] = Field(default="colored")
    LOG_FILE: str | None = Field(default=None)

    ADMIN_USER: str = "admin"
    ADMIN_PASSWORD: SecretStr = SecretStr("admin")
    # Настройки сервера
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DOMAIN: str | None = Field(default=None, description="Application domain URL")

    # JWT Configuration
    SECRET_KEY: str = Field(
        default="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7",
        description="Secret key for JWT token signing",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 1440

    db: DbSettings = Field(default_factory=DbSettings)

    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN: str | None = Field(
        default=None, description="Telegram bot token"
    )
    TELEGRAM_POLLING: bool = Field(default=True, description="Enable polling mode")
    TELEGRAM_WEBHOOK_SECRET: str | None = Field(
        default=None, description="Auto-generated secret for webhook verification"
    )
    TELEGRAM_WEBHOOK_PATH: str = Field(
        default="/telegram/webhook", description="Webhook endpoint path"
    )

    # AI Configuration
    GEMINI_API_KEY: str | None = Field(
        default=None, description="Google Gemini API key for AI service"
    )

    # Настройка для чтения из .env файла
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_nested_delimiter="__"
    )

    def is_bot_enabled(self) -> bool:
        """Check if Telegram bot should be enabled."""
        return bool(self.TELEGRAM_BOT_TOKEN)

    def is_ai_enabled(self) -> bool:
        """Check if AI service should be enabled."""
        return bool(self.GEMINI_API_KEY)


# Создаем экземпляр настроек для использования в проекте
settings = Settings()
