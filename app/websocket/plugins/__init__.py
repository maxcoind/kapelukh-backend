from app.websocket.plugin_system import ModelRegistry, model_registry, ModelPlugin
from app.websocket.plugins.payment_plugin import PaymentPlugin
from app.websocket.plugins.telegram_user_plugin import TelegramUserPlugin
from app.websocket.plugins.survey_plugin import SurveyPlugin


def register_plugins():
    """Register all model plugins."""
    registry = model_registry

    # Register plugins
    registry.register(PaymentPlugin())
    registry.register(TelegramUserPlugin())
    registry.register(SurveyPlugin())


__all__ = [
    "ModelPlugin",
    "ModelRegistry",
    "model_registry",
    "PaymentPlugin",
    "TelegramUserPlugin",
    "SurveyPlugin",
    "register_plugins",
]
