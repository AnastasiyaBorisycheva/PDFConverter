from aiogram import Router, html
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from crud.user import crud_user
from utils.keyboard import main_keyboard
from utils.temp_buffer import create_temp_folder

router = Router()


@router.message(CommandStart())
async def command_start_handler(
        message: Message,
        session: AsyncSession) -> None:
    """
    This handler receives messages with `/start` command
    """

    # Проверяем, есть ли пользователь в БД
    user = await crud_user.get_by_telegram_id(
        telegram_id=message.from_user.id,
        session=session)

    if not user:
        user_dict = {
                "first_name": message.from_user.first_name,
                "last_name": message.from_user.last_name,
                "username": message.from_user.username,
                "is_premium": message.from_user.is_premium
            }
        await crud_user.create_or_update(
            message.from_user.id,
            session,
            **user_dict,)

    create_temp_folder(message.from_user.id)

    await message.answer(
        f"Hello, {html.bold(message.from_user.full_name)}!",
        reply_markup=main_keyboard()
    )
