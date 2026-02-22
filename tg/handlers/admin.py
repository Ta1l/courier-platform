"""
handlers/admin.py — Admin-only handlers.
"""

import logging
import math

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message

from config import ADMIN_ID
from database.db import (
    count_applications,
    get_application_by_id,
    get_applications_page,
    mark_contacted,
)
from keyboards.keyboards import get_contacted_done_keyboard, get_contacted_keyboard

logger = logging.getLogger(__name__)

router = Router(name="admin")

PAGE_SIZE = 10


def _render_application_message(app: dict) -> str:
    status = "✅ Связался" if app["contacted"] else "🆕 Новая"
    username = f"@{app['username']}" if app["username"] else "—"
    return (
        f"📋 <b>Заявка #{app['id']}</b>  —  {status}\n\n"
        f"<b>Имя:</b> {app['first_name'] or '—'}\n"
        f"<b>Username:</b> {username}\n"
        f"<b>Telegram ID:</b> <code>{app['telegram_id']}</code>\n"
        f"<b>Телефон:</b> {app['phone']}\n"
        f"<b>Возраст:</b> {app['age']}\n"
        f"<b>Гражданство:</b> {app['citizenship']}\n"
        f"<b>Source:</b> {app['source'] or '—'}\n"
        f"<b>Дата:</b> {app['submitted_at']}"
    )


@router.message(Command("app"))
async def cmd_app(message: Message, command: CommandObject) -> None:
    """
    Admin command to list applications with pagination.
    Usage: /app [page]
    """
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Эта команда доступна только администратору.")
        return

    page = 1
    if command.args:
        raw_page = command.args.strip()
        if not raw_page.isdigit() or int(raw_page) < 1:
            await message.answer("⚠️ Укажите корректную страницу: <code>/app 1</code>.")
            return
        page = int(raw_page)

    total = await count_applications()
    if total == 0:
        await message.answer("📭 Заявок пока нет.")
        return

    total_pages = max(1, math.ceil(total / PAGE_SIZE))
    if page > total_pages:
        page = total_pages

    offset = (page - 1) * PAGE_SIZE
    applications = await get_applications_page(limit=PAGE_SIZE, offset=offset)

    await message.answer(
        f"📋 <b>Всего заявок:</b> {total}\n"
        f"<b>Страница:</b> {page}/{total_pages} "
        f"(по {PAGE_SIZE} шт.)"
    )

    for app in applications:
        keyboard = (
            get_contacted_done_keyboard()
            if app["contacted"]
            else get_contacted_keyboard(app["id"])
        )
        await message.answer(_render_application_message(app), reply_markup=keyboard)

    if total_pages > 1:
        hints: list[str] = []
        if page > 1:
            hints.append(f"⬅️ <code>/app {page - 1}</code>")
        if page < total_pages:
            hints.append(f"➡️ <code>/app {page + 1}</code>")
        await message.answer(" ".join(hints))


@router.callback_query(F.data.startswith("contacted:"))
async def cb_contacted(callback: CallbackQuery) -> None:
    """
    Handle admin callback that marks application as contacted.
    """
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Только для администратора.", show_alert=True)
        return

    raw = callback.data.split(":", maxsplit=1)[1]
    if raw == "done":
        await callback.answer("✅ Уже отмечено как «Связался».")
        return

    try:
        app_id = int(raw)
    except ValueError:
        await callback.answer("❌ Некорректный ID заявки.", show_alert=True)
        return

    app = await get_application_by_id(app_id)
    if not app:
        await callback.answer("❌ Заявка не найдена.", show_alert=True)
        return

    if app["contacted"]:
        if callback.message:
            await callback.message.edit_reply_markup(
                reply_markup=get_contacted_done_keyboard()
            )
        await callback.answer("✅ Уже отмечено как «Связался».")
        return

    updated = await mark_contacted(app_id)
    if not updated:
        await callback.answer("❌ Не удалось обновить статус, попробуйте снова.", show_alert=True)
        return

    app["contacted"] = 1
    if callback.message:
        try:
            await callback.message.edit_text(
                text=_render_application_message(app),
                reply_markup=get_contacted_done_keyboard(),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to refresh application message #%s: %s", app_id, exc)
            await callback.message.edit_reply_markup(
                reply_markup=get_contacted_done_keyboard()
            )

    await callback.answer("✅ Статус обновлён: Связался.")
    logger.info("Application #%s marked as contacted.", app_id)
