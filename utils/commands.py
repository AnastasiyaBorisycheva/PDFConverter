from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault

from core.logger import setup_logger


logger = setup_logger(__name__)

commands = [
    BotCommand(
        command="start",
        description="Зарегистрируйся в боте"
    ),
    BotCommand(
        command="convert",
        description="Конвертировать все присланные файлы в pdf"
    ),
]


async def set_common_commands(bot: Bot):
    logger.info("Устанавливаю команды")
    await bot.set_my_commands(
        commands=commands,
        scope=BotCommandScopeDefault()
    )
    logger.info("Команды установлены")
