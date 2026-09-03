from aiogram import Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from core.logger import setup_logger

logger = setup_logger(__name__)

router = Router()


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    """Обработчик команды /help с инструкцией и контактами."""

    logger.info(f"Пользователь {message.from_user.id} вызвал команду /help")
    
    text = (
        "<b>Как пользоваться ботом:</b>\n\n"
        "1. Отправь мне одно или несколько изображений (как <b>фото</b> или как <b>документ</b>).\n"
        "2. Отправь команду <code>/convert</code>.\n"
        "3. Бот сожмет картинки, исправит ориентацию и пришлет готовый <b>PDF</b>.\n"
        "4. Чтобы сбросить загруженные файлы без конвертации, используй <code>/clear</code>.\n\n"
        "<b>Разработчик:</b> @Anastasiia_Mist\n"
        "Пишите по вопросам работы бота, предложениям или баг-репортам!"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Исходный код на GitHub",
                    url="https://github.com/AnastasiyaBorisycheva/PDFConverter"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Написать в ЛС",
                    url="https://t.me/Anastasiia_Mist"
                )
            ]
        ]
    )

    await message.answer(
        text=text,
        parse_mode="html",
        reply_markup=keyboard,
        disable_web_page_preview=True
    )