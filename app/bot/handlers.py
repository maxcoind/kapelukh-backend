from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.crud.survey import save_user_survey
from app.crud.telegram_user import (
    create_telegram_user,
    get_telegram_user,
    update_last_interaction,
)
from app.schemas.telegram_user import TelegramUserCreate

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    """Handle /start command."""
    if not message.from_user:
        await message.answer("Error: Unable to identify user.")
        return
    user = await get_telegram_user(session, message.from_user.id)
    if user:
        await message.answer("✨ Радий знову вітати Вас!")
        return
    user_data = TelegramUserCreate(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        language_code=message.from_user.language_code,
        is_bot=message.from_user.is_bot,
    )

    await create_telegram_user(session, user_data)
    await update_last_interaction(session, message.from_user.id)

    await message.answer("""✨ Вітаю! Зафіксуйте своє Волевиявлення:
        - ПІБ та Династія — Ваше ім'я, по батькові та назва роду.
        - Суперсила — Ваші головні таланти та те, що робите найкраще.
        - Дата народження — Бажано у форматі ДД.ММ.РРРР.
        - Вдосконалення — Якості характеру, які прагнете покращити.
        - Купівля — Що плануєте придбати найближчим часом.
        - Продаж — Що ви пропонуєте світу (товари/послуги).
        - Служіння — Що ви готові дарувати або чим служити суспільству.
        - Матеріальна мета — Ваші масштабні майнові цілі.
        - Соціальна ціль — Що хочете зробити для людей та громади.
        - Духовна ціль — Ваше бачення вічності та шлях до цілісності.
        🌿 Пишіть від серця, у вільній формі. Я прийму ваш намір таким, яким він є зараз.
        """)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    await message.answer(
        "Available commands:\n"
        "/start - Register and start using the bot\n"
        "/help - Show this help message\n"
        "/status - Check your account status"
    )


@router.message(Command("status"))
async def cmd_status(message: Message, session: AsyncSession):
    """Handle /status command."""
    if not message.from_user:
        await message.answer("Error: Unable to identify user.")
        return

    from app.crud.telegram_user import get_telegram_user

    user = await get_telegram_user(session, message.from_user.id)

    if user:
        await update_last_interaction(session, message.from_user.id)

        status_text = "✅ Active" if user.is_active else "❌ Inactive"
        await message.answer(
            f"📊 Your account status:\n"
            f"ID: {user.telegram_id}\n"
            f"Username: @{user.username or 'N/A'}\n"
            f"Status: {status_text}\n"
            f"Registered: {user.created_at.strftime('%Y-%m-%d %H:%M') if user.created_at else 'N/A'}\n"
            f"Last interaction: {user.last_interaction_at.strftime('%Y-%m-%d %H:%M') if user.last_interaction_at else 'Never'}"
        )
    else:
        await message.answer("Account not found. Please use /start to register.")


@router.message()
async def handle_survey(message: Message, session: AsyncSession):
    """Handle survey submissions from non-command messages."""
    if not message.from_user:
        await message.answer("Error: Unable to identify user.")
        return

    if not message.text:
        await message.answer("Please send a text message.")
        return

    if not settings.is_ai_enabled():
        await message.answer("AI service is currently not available.")
        return

    user = await get_telegram_user(session, message.from_user.id)
    if not user:
        user_data = TelegramUserCreate(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            language_code=message.from_user.language_code,
            is_bot=message.from_user.is_bot,
        )
        user = await create_telegram_user(session, user_data)

    await update_last_interaction(session, message.from_user.id)

    status_msg = await message.answer("✨ Приймаю ваше волевиявлення...")

    try:
        from app.services.survey_ai import process_soft_survey

        result = await process_soft_survey(message.text)

        if result.is_valid:
            await save_user_survey(
                session=session,
                user_id=message.from_user.id,
                validation_result=result,
            )

            first_name = result.data.full_name.get("first_name", "Друже")
            response = f"🙏 Дякую, {first_name}, вашу анкету прийнято."

            if result.suggestions:
                response += f"\n\nПорада від серця: {result.suggestions}"

            await status_msg.edit_text(response)
        else:
            await status_msg.edit_text(
                "Здається, ви надіслали щось інше. Будь ласка, надішліть вашу анкету."
            )
    except Exception as e:
        from app.logger import get_logger

        logger = get_logger(__name__)
        logger.error(f"Error processing survey: {e}")
        await status_msg.edit_text(
            "Вибачте, сталася помилка при обробці вашої анкети. Спробуйте пізніше."
        )
