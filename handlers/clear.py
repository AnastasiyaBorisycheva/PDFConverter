from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import setup_logger
from crud.user import crud_user
from utils.temp_buffer import delete_files_in_folder

logger = setup_logger(__name__)


router = Router()

@router.message(Command("clear"))
async def clear_handler(
        message: Message,
        session: AsyncSession) -> None:
    """
    This handler receives messages with `/clear` command
    """

    logger.info(f"Пользователь {message.from_user.id} вызвал команду /clear")

    # Удаляем все временные файлы пользователя
    user_id = message.from_user.id
    delete_files_in_folder(f'temp/{user_id}/input')
    delete_files_in_folder(f'temp/{user_id}/output')
    logger.info(f"Пользователь {user_id} очистил временные файлы на диске")

    await message.answer(
        "Все временные файлы удалены.",
        reply_markup=None
    )
