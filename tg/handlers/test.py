"""
handlers/test.py — FSM handlers for the step-by-step application test.
Handles phone contact, name input, age input, citizenship selection,
validation, database saving, and admin notification.
"""

import logging
import re
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from states.application import ApplicationForm
from keyboards.keyboards import (
    get_contact_keyboard,
    get_citizenship_keyboard,
    get_contacted_keyboard,
)
from database.db import save_application
from config import ADMIN_ID

logger = logging.getLogger(__name__)

# Create a router for the test flow
router = Router(name="test")

# List of allowed citizenships (EAEU member states)
ALLOWED_CITIZENSHIPS: list[str] = [
    "Российская Федерация",
    "Республика Беларусь",
    "Республика Казахстан",
    "Республика Армения",
    "Кыргызская Республика",
]


def normalize_phone(raw_phone: str) -> str:
    """
    Normalize phone number to a compact international form.
    """
    cleaned = raw_phone.strip()
    if cleaned.startswith("+"):
        digits = re.sub(r"\D", "", cleaned[1:])
        return f"+{digits}"

    digits = re.sub(r"\D", "", cleaned)
    if len(digits) == 11 and digits.startswith("8"):
        digits = f"7{digits[1:]}"
    if len(digits) == 11 and digits.startswith("7"):
        return f"+{digits}"
    if len(digits) == 10:
        return f"+7{digits}"
    return f"+{digits}" if digits else ""


def is_valid_phone(phone: str) -> bool:
    digits = re.sub(r"\D", "", phone)
    return 10 <= len(digits) <= 15


def normalize_name(raw_name: str) -> str:
    """
    Normalize user-entered name: trim and collapse extra spaces.
    """
    return " ".join(raw_name.strip().split())


def is_valid_name(name: str) -> bool:
    """
    Validate a name entered by user.
    Allowed chars: letters, spaces, hyphen and apostrophe.
    """
    if not name or len(name) < 2 or len(name) > 80:
        return False

    letters = 0
    for char in name:
        if char.isalpha():
            letters += 1
            continue
        if char in " -'":
            continue
        return False
    return letters >= 2


# ── Step 0: Start the test (callback from inline button) ──────────

@router.callback_query(F.data == "start_test")
async def cb_start_test(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Handle the 'Пройти тест' inline button press.
    Transition to the first FSM state and request the user's phone contact.
    """
    await callback.message.answer(
        "📋 <b>Шаг 1 из 4</b>\n\n"
        "Пожалуйста, отправьте ваш контактный номер телефона, "
        "нажав кнопку ниже.",
        reply_markup=get_contact_keyboard(),
    )
    await state.set_state(ApplicationForm.waiting_for_phone)
    await callback.answer()


# ── Step 1: Receive phone contact ─────────────────────────────────

@router.message(ApplicationForm.waiting_for_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext) -> None:
    """
    Handle a valid contact message (user shared their phone number).
    Save the phone and move to the name step.
    """
    contact = message.contact
    if contact.user_id and contact.user_id != message.from_user.id:
        logger.warning(
            "User %s sent чужой контакт user_id=%s",
            message.from_user.id,
            contact.user_id,
        )
        await message.answer(
            "⚠️ Отправьте, пожалуйста, именно свой контакт через кнопку ниже.",
            reply_markup=get_contact_keyboard(),
        )
        return

    phone = normalize_phone(contact.phone_number)
    if not is_valid_phone(phone):
        logger.warning(
            "User %s sent invalid phone format: %s",
            message.from_user.id,
            contact.phone_number,
        )
        await message.answer(
            "⚠️ Не удалось распознать номер. Повторите отправку через кнопку ниже.",
            reply_markup=get_contact_keyboard(),
        )
        return

    await state.update_data(phone=phone)

    # Remove the reply keyboard and ask for name
    await message.answer(
        "📋 <b>Шаг 2 из 4</b>\n\n"
        "Как вас зовут? Укажите имя и фамилию.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(ApplicationForm.waiting_for_name)


@router.message(ApplicationForm.waiting_for_phone)
async def process_phone_invalid(message: Message) -> None:
    """
    Handle any message that is NOT a contact while waiting for phone.
    Remind the user to use the button.
    """
    await message.answer(
        "⚠️ Пожалуйста, используйте кнопку «📱 Отправить контакт» ниже, "
        "чтобы поделиться вашим номером телефона.",
        reply_markup=get_contact_keyboard(),
    )


# ── Step 2: Receive and validate name ─────────────────────────────

@router.message(ApplicationForm.waiting_for_name)
async def process_name(message: Message, state: FSMContext) -> None:
    """
    Handle name input and move to age step.
    """
    raw_text = message.text or ""
    name = normalize_name(raw_text)

    if not is_valid_name(name):
        await message.answer(
            "⚠️ Укажите корректное имя: от 2 до 80 символов, только буквы, пробел, дефис или апостроф."
        )
        return

    await state.update_data(first_name=name)
    await message.answer(
        "📋 <b>Шаг 3 из 4</b>\n\n"
        "Укажите ваш возраст (полных лет):"
    )
    await state.set_state(ApplicationForm.waiting_for_age)


# ── Step 3: Receive and validate age ──────────────────────────────

@router.message(ApplicationForm.waiting_for_age)
async def process_age(message: Message, state: FSMContext) -> None:
    """
    Handle age input. Validates:
    - Must be a positive integer
    - Must be 16 or older
    """
    # Validate that the input is a number
    if not message.text or not message.text.strip().isdigit():
        await message.answer(
            "⚠️ Пожалуйста, введите ваш возраст числом (например, 21)."
        )
        return

    age = int(message.text.strip())

    # Validate age range (reasonable bounds)
    if age < 1 or age > 120:
        await message.answer(
            "⚠️ Пожалуйста, укажите корректный возраст."
        )
        return

    # Check minimum age requirement (16+)
    if age < 16:
        await message.answer(
            "❌ К сожалению, вы не подходите по возрасту "
            "для подачи заявки.\n"
            "Минимальный возраст — 16 лет."
        )
        # Clear FSM state — do NOT save to database
        await state.clear()
        return

    # Age is valid — save and proceed to citizenship
    await state.update_data(age=age)

    await message.answer(
        "📋 <b>Шаг 4 из 4</b>\n\n"
        "Выберите ваше гражданство:",
        reply_markup=get_citizenship_keyboard(),
    )
    await state.set_state(ApplicationForm.waiting_for_citizenship)


# ── Step 4a: "Нет из выше перечисленных" — reject ─────────────────

@router.callback_query(
    ApplicationForm.waiting_for_citizenship,
    F.data == "citizenship:none",
)
async def process_citizenship_none(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Handle the 'Нет из выше перечисленных' button press.
    Reject the application immediately and clear FSM.
    """
    await callback.message.answer(
        "❌ К сожалению продолжить тест нельзя."
    )
    # Clear FSM state — do NOT save to database
    await state.clear()
    await callback.answer()


# ── Step 4b: Receive and validate citizenship ──────────────────────

@router.callback_query(
    ApplicationForm.waiting_for_citizenship,
    F.data.startswith("citizenship:"),
)
async def process_citizenship(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Handle citizenship selection from inline keyboard.
    Validates against the allowed list, then saves and notifies admin.
    """
    citizenship = callback.data.split(":", maxsplit=1)[1]

    # Validate citizenship (should always pass if using our keyboard,
    # but we check defensively)
    if citizenship not in ALLOWED_CITIZENSHIPS:
        await callback.message.answer(
            "❌ К сожалению, вы не подходите по гражданству "
            "для подачи заявки."
        )
        await state.clear()
        await callback.answer()
        return

    # Gather all collected data from FSM storage
    data = await state.get_data()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Build the application record
    application = {
        "telegram_id": callback.from_user.id,
        "username": callback.from_user.username or "",
        "first_name": data.get("first_name") or callback.from_user.first_name or "",
        "phone": data.get("phone", ""),
        "age": data.get("age", 0),
        "citizenship": citizenship,
        "source": data.get("source") or "",
        "campaign_id": data.get("campaign_id"),
        "status": "new",
        "revenue": None,
        "submitted_at": now,
    }

    # ── Save to SQLite ──
    app_id = await save_application(application)
    logger.info(
        "Application saved (id=%s): telegram_id=%s, name=%s",
        app_id,
        application["telegram_id"],
        application["first_name"],
    )

    # ── Notify the admin with "Связался" button ──
    admin_text = (
        "📋 <b>Новая заявка:</b>\n\n"
        f"<b>Имя:</b> {application['first_name']}\n"
        f"<b>Username:</b> @{application['username'] or '—'}\n"
        f"<b>Telegram ID:</b> <code>{application['telegram_id']}</code>\n"
        f"<b>Телефон:</b> {application['phone']}\n"
        f"<b>Возраст:</b> {application['age']}\n"
        f"<b>Гражданство:</b> {application['citizenship']}\n"
        f"<b>Source:</b> {application['source'] or '—'}\n"
        f"<b>Submitted at:</b> {application['submitted_at']}"
    )

    try:
        await callback.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            reply_markup=get_contacted_keyboard(app_id),
        )
        logger.info("Admin notified successfully (ID=%s).", ADMIN_ID)
    except Exception as exc:
        logger.error("Failed to notify admin (ID=%s): %s", ADMIN_ID, exc)

    # ── Confirm to the applicant ──
    await callback.message.answer(
        "✅ Спасибо! Ваша заявка принята.\n"
        "Мы свяжемся с вами в ближайшее время."
    )

    # Clear FSM state — flow is complete
    await state.clear()
    await callback.answer()
