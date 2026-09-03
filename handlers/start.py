from datetime import datetime, timezone

from aiogram import Router, html
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from crud.user import crud_user
from core.logger import setup_logger
from utils.keyboard import main_keyboard

logger = setup_logger(name=__name__)

router = Router()


@router.message(CommandStart())
async def command_start_handler(
        message: Message,
        session: AsyncSession) -> None:
    """
    This handler receives messages with `/start` command
    """

    logger.info(f"Пользователь {message.from_user.id} вызвал команду /start")

    # Автоматически создаст нового юзера или обновит username/first_name существующего
    user = await crud_user.create_or_update(
        telegram_id=message.from_user.id,
        session=session,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        is_premium=message.from_user.is_premium
    )
    await message.answer(f"Привет, {user.first_name}!")
