from app.api.auth import router as auth_router
from app.api.payments import router as payments_router
from app.api.telegram_users import router as telegram_users_router
from app.api.survey import router as survey_router

__all__ = ["auth_router", "payments_router", "telegram_users_router", "survey_router"]
