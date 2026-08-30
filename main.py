import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from core.core import TOKEN
from core.logger import setup_logger
from database.engine import AsyncSessionLocal
from handlers.clear import router as clear_router
from handlers.pdf_working import router as pdf_router
from handlers.repeater import router as repeater_router
from handlers.start import router as start_router
from middlewares.db import DbSessionMiddleware
from utils.commands import set_common_commands

# Инициализация логгера
logger = setup_logger(__name__)


async def on_startup(bot: Bot) -> None:
    """Действия при запуске бота."""
    await set_common_commands(bot)
    logger.info("Команды Telegram-бота успешно обновлены")


async def main() -> None:
    dp = Dispatcher()

    # Инициализация бота с парсингом HTML
    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Регистрация Middlewares
    dp.update.outer_middleware(DbSessionMiddleware(session_pool=AsyncSessionLocal))

    # Регистрация Startup-событий
    dp.startup.register(on_startup)

    # Подключение роутеров
    dp.include_router(start_router)
    dp.include_router(pdf_router)
    dp.include_router(clear_router)
    dp.include_router(repeater_router)
    logger.info("Роутеры загружены")

    try:
        # Сбрасываем старые накопившиеся сообщения до запуска
        await bot.delete_webhook(drop_pending_updates=True)
        
        logger.info("Запуск поллинга...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Критическая ошибка при работе бота: {e}", exc_info=True)
    finally:
        # Graceful shutdown: аккуратно закрываем сессию бота
        await bot.session.close()
        logger.info("Сессия бота закрыта")


if __name__ == "__main__":
    try:
        logger.info("Starting bot...")
        asyncio.run(main(), debug=False)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot execution stopped by user signal.")
