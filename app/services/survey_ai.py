from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from app.config import settings
from app.logger import get_logger
from app.schemas.survey import ValidationResult

logger = get_logger(__name__)

_model = None
_soft_survey_agent = None


def _initialize_ai():
    global _model, _soft_survey_agent
    provider = GoogleProvider(api_key=settings.GEMINI_API_KEY)
    _model = GoogleModel("gemini-3-flash-preview", provider=provider)
    _soft_survey_agent = Agent(
        _model,
        output_type=ValidationResult,
        system_prompt=(
            "Ти — мудрий та м'який провідник. Твоя мета — прийняти волевиявлення людини таким, яким воно є. "
            "ПРАВИЛА: "
            "1. Сприймай дані ПІБ та дату народження як істинні, навіть якщо вони неповні (наприклад, тільки число). Не вимагай виправлень. "
            "2. Встановлюй is_valid=True майже завжди, якщо людина намагалася заповнити анкету. "
            "3. Тільки якщо повідомлення — це повний спам або набір випадкових літер, став is_valid=False. "
            "4. Якщо якісь поля залишилися порожніми або цілі дуже короткі, просто додай м'яку пораду у поле suggestions. "
            "5. Тон має бути поважним, теплим та підтримуючим. Мова — українська."
        ),
    )


def is_ai_available() -> bool:
    return settings.is_ai_enabled()


async def process_soft_survey(text: str) -> ValidationResult:
    if not is_ai_available():
        raise RuntimeError(
            "AI service is not available. Please check GEMINI_API_KEY configuration."
        )

    if _soft_survey_agent is None:
        _initialize_ai()

    if _soft_survey_agent is None:
        raise RuntimeError("AI agent is not initialized.")
    result = await _soft_survey_agent.run(text)
    return result.output
