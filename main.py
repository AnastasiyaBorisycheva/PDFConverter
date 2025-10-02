import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from core.core import TOKEN
from core.logger import setup_logger
from database.init_db import create_tables
from handlers.pdf_working import router as pdf_router
from handlers.repeater import router as repeater_router
from handlers.start import router as start_router
from middlewares.db import DbSessionMiddleware
from utils.commands import set_common_commands

# Инициализация логгера
logger = setup_logger(__name__)


async def on_startup(bot: Bot):
    await set_common_commands(bot)
    logger.info("Команды настроены")


async def main() -> None:
    dp = Dispatcher()
    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp.update.outer_middleware(DbSessionMiddleware())

    dp.startup.register(on_startup)

    # Подключаем все роутеры
    dp.include_router(start_router)
    dp.include_router(pdf_router)
    dp.include_router(repeater_router)
    logger.info("Роутеры загружены")

    await create_tables()
    await dp.start_polling(bot)


if __name__ == "__main__":
    logger.info("Starting bot...")
    asyncio.run(main(), debug=False)
    logger.info("Bot stopped.")
