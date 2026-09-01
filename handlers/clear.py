import asyncio
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from core.logger import setup_logger
from utils.temp_buffer import remove_user_temp_dir

logger = setup_logger(__name__)

router = Router()


@router.message(Command("clear"))
async def clear_handler(message: Message) -> None:
    """Обработчик команды /clear для полной очистки временных файлов пользователя."""
    user_id = message.from_user.id
    logger.info(f"Пользователь {user_id} вызвал команду /clear")

    # Безопасно и неблокирующе удаляем всю временную директорию пользователя
    await asyncio.to_thread(remove_user_temp_dir, user_id)
    
    logger.info(f"Временные файлы пользователя {user_id} успешно удалены")

    await message.answer(
        "<b>Все загруженные и обработанные файлы удалены!</b>\n"
        "Вы можете отправить новую партию изображений.",
        parse_mode="html",
        reply_markup=None
    )
