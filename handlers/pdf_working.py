import asyncio
from datetime import datetime, timezone
from pathlib import Path

from aiogram import Bot, F, Router, html
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
    TelegramNetworkError,
    TelegramRetryAfter,
)
from aiogram.types import FSInputFile, Message
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import setup_logger
from crud.converting import crud_converting
from crud.user import crud_user
from utils.image_converter import convert_images_to_pdf
from utils.temp_buffer import get_user_temp_paths, remove_user_temp_dir

# Допустимые расширения файлов изображений
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".heic"}

logger = setup_logger(name=__name__)

router = Router()


@router.message(F.document | F.photo)
async def media_handler(message: Message, bot: Bot) -> None:
    """Сохранение валидных изображений во временную папку по ID пользователя."""
    user_id = message.from_user.id
    logger.info(f"Получен медиафайл от пользователя {user_id}")

    path_in, _ = get_user_temp_paths(user_id)
    document = None
    document_name = None

    # 1. Валидация и извлечение данных
    if message.photo:
        document = message.photo[-1]
        document_name = f"{document.file_unique_id}.jpg"
    elif message.document:
        doc = message.document
        doc_name = doc.file_name or f"doc_{message.message_id}.jpg"
        ext = Path(doc_name).suffix.lower()
        mime_type = doc.mime_type or ""

        # Проверяем расширение файла и MIME-тип
        if ext not in ALLOWED_EXTENSIONS and not mime_type.startswith("image/"):
            logger.warning(
                f"Пользователь {user_id} отправил неподдерживаемый файл: {doc_name} ({mime_type})"
            )
            await message.reply(
                f"Файл <b>{html.quote(doc_name)}</b> не является поддерживаемым изображением.\n\n"
                f"Пожалуйста, отправляйте только картинки форматов: <code>JPG, PNG, WEBP, BMP, TIFF</code>."
            )
            return

        document = doc
        document_name = doc_name or f"doc_{message.message_id}.jpg"

    if not document:
        return

    # 2. Сохранение файла
    msg = await message.answer("Увидел картинку, сохраняю...")

    try:
        filename = f"{message.message_id}_{document_name}"
        filepath = path_in / filename

        logger.debug(f"Скачивание файла в {filepath}")
        await bot.download(document.file_id, destination=filepath)
        logger.info(f"Файл успешно сохранён: {html.code(document_name)}")

        await msg.edit_text("Файл сохранён")
        await asyncio.sleep(1)
        await msg.delete()

    except Exception as e:
        logger.error(f"Ошибка при сохранении файла: {e}", exc_info=True)
        await msg.edit_text("Произошла ошибка при сохранении файла.")



async def send_file_with_retry(
    message: Message,
    file_path: str | Path,
    caption: str = None,
    max_retries: int = 3,
) -> bool:
    """Отправка файла с повторными попытками и логированием."""
    path = Path(file_path)
    logger.info(f"Начало отправки файла {path}")

    for attempt in range(1, max_retries + 1):
        try:
            logger.debug(f"Попытка {attempt}/{max_retries} отправки файла")
            file_to_send = FSInputFile(path)

            await message.answer_document(
                document=file_to_send,
                caption=caption,
                reply_markup=None,
            )

            file_size_kb = path.stat().st_size / 1024
            logger.info(f"Файл успешно отправлен! Размер: {file_size_kb:.2f} KB, попытка: {attempt}")
            return True

        except TelegramRetryAfter as e:
            logger.warning(f"Flood control. Ждём {e.retry_after} сек (попытка {attempt}/{max_retries})")
            await asyncio.sleep(e.retry_after)

        except TelegramNetworkError as e:
            logger.warning(f"Сетевая ошибка: {e}. Попытка {attempt}/{max_retries}")
            if attempt < max_retries:
                await asyncio.sleep(2**attempt)

        except TelegramBadRequest as e:
            logger.error(f"Bad request ошибка: {e}", exc_info=True)
            break

        except (TelegramAPIError, Exception) as e:
            logger.error(f"Ошибка при отправке: {e}", exc_info=True)
            if attempt < max_retries:
                await asyncio.sleep(3)

    return False


@router.message(F.text.lower().contains("convert"))
async def pdf_converter_handler(message: Message, session: AsyncSession) -> None:
    """Обработчик конвертации PDF."""
    user_id = message.from_user.id
    logger.info(f"=== НАЧАЛО КОНВЕРТАЦИИ для пользователя {user_id} ===")
    start_time = asyncio.get_running_loop().time()

    msg = await message.answer("Начинаю конвертацию ваших файлов... ⏳")

    # Пауза для дозагрузки медиагрупп при массовой отправке
    await asyncio.sleep(2)

    # Проверка / создание пользователя в БД
    user = await crud_user.get_by_telegram_id(telegram_id=user_id, session=session)
    if not user:
        user_dict = {
            "first_name": message.from_user.first_name,
            "last_name": message.from_user.last_name,
            "username": message.from_user.username,
            "is_premium": message.from_user.is_premium,
            "registration_date": datetime.now(timezone.utc),
        }
        user = await crud_user.create_or_update(user_id, session, **user_dict)

    path_in, path_out = get_user_temp_paths(user_id)

    # Получаем список файлов из входной директории
    files_in_folder = [f for f in path_in.iterdir() if f.is_file()] if path_in.exists() else []
    file_count = len(files_in_folder)

    if file_count == 0:
        logger.warning(f"Нет файлов для конвертации у пользователя {user_id}")
        await msg.edit_text("Нет загруженных файлов для конвертации")
        return

    await message.answer(f"Найдено файлов для конвертации: {file_count}")

    # Конвертация файлов через неблокирующую асинхронную обертку
    try:
        result_filename = await convert_images_to_pdf(
            input_directory=path_in,
            output_directory=path_out,
            message_id=message.message_id,
            quality=100,
            max_width=1200,
            max_height=1800,
        )

        if not result_filename or not Path(result_filename).exists():
            raise FileNotFoundError("Результирующий PDF файл не был сформирован")

        file_size_kb = Path(result_filename).stat().st_size / 1024
        logger.info(f"PDF сформирован. Размер: {file_size_kb:.2f} KB")
        await msg.edit_text("Конвертация завершена. Результат готов к отправке!")

    except Exception as e:
        logger.error(f"Ошибка при конвертации: {e}", exc_info=True)
        await message.answer("Ошибка при конвертации файлов")
        return

    # Отправка результативного файла
    caption = f"Конвертировано файлов: {file_count}"
    success = await send_file_with_retry(message, result_filename, caption=caption)

    # Сохранение записи о с конвертации в БД
    data = {
        "telegram_id": user_id,
        "user_id": user.id,
        "is_premium": message.from_user.is_premium,
        "number_of_files": file_count,
        "file_size": Path(result_filename).stat().st_size,
        "converted_at": datetime.now(timezone.utc),
    }
    await crud_converting.create(session=session, data=data)

    # Очистка временных директорий только при успехе
    if success:
        remove_user_temp_dir(user_id)
        logger.debug(f"Временная папка пользователя {user_id} полностью очищена")
    else:
        logger.warning(f"Папка пользователя {user_id} сохранена для повторной попытки")
        try:
            await message.answer(
                "<b>Ошибка отправки</b>\n"
                "Не удалось отправить файл из-за проблем с сетью.\n"
                "<b>Ваши файлы сохранены!</b>\n\n"
                "Просто отправьте команду /convert ещё раз, когда соединение восстановится.\n"
                "Повторно загружать изображения <b>не нужно</b>.",
                parse_mode="html",
            )
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение об ошибке: {e}")

    elapsed_time = asyncio.get_running_loop().time() - start_time
    logger.info(f"=== ЗАВЕРШЕНО для {user_id} за {elapsed_time:.2f}с (успех: {success}) ===")