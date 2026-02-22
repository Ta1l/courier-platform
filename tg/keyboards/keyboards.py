"""
keyboards/keyboards.py — Keyboard builders for inline and reply keyboards.
Contains all keyboard markup used throughout the bot.
"""

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)


def get_start_keyboard() -> InlineKeyboardMarkup:
    """
    Build the /start message inline keyboard with two buttons:
    - "Общая информация" — opens an external URL
    - "Пройти тест" — triggers the FSM test flow via callback
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Общая информация",
                    url="https://kurer-spb.ru/",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Пройти тест",
                    callback_data="start_test",
                ),
            ],
        ]
    )


def get_contact_keyboard() -> ReplyKeyboardMarkup:
    """
    Build a reply keyboard with a single button that requests
    the user's phone contact via Telegram's built-in mechanism.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📱 Отправить контакт",
                    request_contact=True,
                ),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_citizenship_keyboard() -> InlineKeyboardMarkup:
    """
    Build an inline keyboard with allowed EAEU citizenships
    plus a 'None of the above' rejection button.
    Each citizenship button sends callback_data 'citizenship:<name>'.
    The rejection button sends callback_data 'citizenship:none'.
    """
    citizenships = [
        "Российская Федерация",
        "Республика Беларусь",
        "Республика Казахстан",
        "Республика Армения",
        "Кыргызская Республика",
    ]
    buttons = [
        [
            InlineKeyboardButton(
                text=name,
                callback_data=f"citizenship:{name}",
            )
        ]
        for name in citizenships
    ]
    # Add the "none of the above" button at the bottom
    buttons.append(
        [
            InlineKeyboardButton(
                text="❌ Нет из выше перечисленных",
                callback_data="citizenship:none",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_contacted_keyboard(app_id: int) -> InlineKeyboardMarkup:
    """
    Build an inline keyboard with a single 'Связался' button
    for the admin to mark an application as contacted.

    Args:
        app_id: Database row ID of the application.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📞 Связался",
                    callback_data=f"contacted:{app_id}",
                ),
            ],
        ]
    )


def get_contacted_done_keyboard() -> InlineKeyboardMarkup:
    """
    Build an inline keyboard showing the 'contacted' status
    as a non-clickable indicator (callback still handled gracefully).
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Связался",
                    callback_data="contacted:done",
                ),
            ],
        ]
    )
