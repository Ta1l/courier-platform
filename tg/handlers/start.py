"""
Handler for /start command.

Preserves existing source tracking and adds optional campaign validation.
"""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database.db import get_active_campaign, parse_campaign_id_from_source
from keyboards.keyboards import get_start_keyboard

router = Router(name="start")
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    """
    Handle /start command and persist deep-link payload in FSM.

    - Legacy behavior is preserved: `source` is always stored as-is.
    - If payload contains campaign id, it is validated against active campaigns.
    """
    await state.clear()

    args = (message.text or "").split(maxsplit=1)
    source = args[1].strip() if len(args) > 1 else None

    campaign_id = parse_campaign_id_from_source(source)
    validated_campaign_id: int | None = None
    if campaign_id is not None:
        campaign = await get_active_campaign(campaign_id)
        if campaign:
            validated_campaign_id = campaign_id
            logger.info(
                "Start payload accepted for campaign_id=%s user_id=%s",
                campaign_id,
                message.from_user.id if message.from_user else None,
            )
        else:
            logger.warning(
                "Invalid or inactive campaign in start payload: %s (user_id=%s)",
                source,
                message.from_user.id if message.from_user else None,
            )

    await state.update_data(source=source, campaign_id=validated_campaign_id)

    await message.answer(
        "Это бот для подачи заявки на работу курьером.\n"
        "Пройдите тест, чтобы отправить заявку.",
        reply_markup=get_start_keyboard(),
    )

