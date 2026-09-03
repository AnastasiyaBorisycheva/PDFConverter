from aiogram import Router
from aiogram.types import Message
from core.logger import setup_logger


logger = setup_logger(name=__name__)

router = Router()


@router.message()
async def echo_handler(message: Message) -> None:
    """
    Handler will forward receive a message back to the sender

    By default, message handler will handle all message types (like a text, photo, sticker etc.)
    """

    logger.info(f"Пользователь {message.from_user.id} получил repeater")

    try:
        # Send a copy of the received message
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        # But not all the types is supported to be copied so need to handle it
        await message.answer("Не могу обработать команду")
