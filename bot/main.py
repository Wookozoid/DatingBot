import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import ErrorEvent

from bot.config import settings
from bot.handlers.browsing import router as browsing_router
from bot.handlers.onboarding import router as onboarding_router
from bot.handlers.profile import router as profile_router
from bot.logger import setup_logging
from bot.services.embedding import get_embedding_service
from storage.database import init_db

logger = logging.getLogger(__name__)

dp = Dispatcher()
dp.include_router(onboarding_router)
dp.include_router(browsing_router)
dp.include_router(profile_router)


@dp.errors()
async def handle_errors(event: ErrorEvent) -> None:
    """
    Ловит любое необработанное исключени пишет его в лог.
    """
    logger.exception(
        "Ошибка при обработке апдейта %s: %s",
        event.update.update_id,
        event.exception,
    )


async def main() -> None:
    setup_logging()

    await init_db()
    logger.info("База данных готова")

    get_embedding_service()
    logger.info("Модель эмбеддингов готова")

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    logger.info("Бот запускается...")
    try:
        await dp.start_polling(bot)
    finally:
        logger.info("Бот остановлен")


if __name__ == "__main__":
    asyncio.run(main())
