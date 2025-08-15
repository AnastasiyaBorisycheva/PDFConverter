from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_keyboard():

    button = KeyboardButton(
        text='Конвертировать присланные файлы в pdf (convert)'
    )
    markup = ReplyKeyboardMarkup(
        keyboard=[[button,],],
        is_persistent=True,
        resize_keyboard=True
    )

    return markup
