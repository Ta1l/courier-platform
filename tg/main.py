"""
main.py — Entry point of the Courier Application Bot.
Initializes the bot, dispatcher, registers routers, and starts polling.
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

try:
    from config import BOT_TOKEN
except RuntimeError as exc:
    raise SystemExit(f"Configuration error: {exc}") from exc
from database.db import init_db
from handlers import start, test, admin

# Configure logging to see bot activity in the console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Main async function: init DB, create bot, register handlers, start polling."""

    # Initialize the SQLite database (create tables if they don't exist)
    await init_db()
    logger.info("Database initialized successfully.")

    # Create the Bot instance with default HTML parse mode
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Create the Dispatcher (manages updates and routers)
    dp = Dispatcher()

    # Register handler routers
    dp.include_router(start.router)   # /start command handler
    dp.include_router(test.router)    # FSM test flow handlers
    dp.include_router(admin.router)   # /app admin command + contacted callbacks

    logger.info("Bot is starting polling...")

    # Start long-polling (blocks until stopped)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
