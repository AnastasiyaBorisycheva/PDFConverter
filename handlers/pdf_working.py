import asyncio
import os
from pathlib import Path
from time import sleep

from aiogram import Bot, F, Router, html
from aiogram.exceptions import (TelegramAPIError, TelegramBadRequest,
                                TelegramNetworkError, TelegramRetryAfter)
from aiogram.types import FSInputFile, Message
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import setup_logger
from crud.converting import crud_convert
from crud.user import crud_user
from utils.image_converter import image_converter_to_pdf
from utils.temp_buffer import create_temp_folder, delete_files_in_folder

logger = setup_logger(name=__name__)

router = Router()


@router.message(F.document | F.photo)
async def media_handler(message: Message, bot: Bot) -> None:
    """Сохранение файлов в темповую папку по ID пользователя."""

    user_id = message.from_user.id
    logger.info(f"Получен файл от пользователя {user_id}")

    path_in, path_out = create_temp_folder(user_id)
    logger.debug(f"Созданы временные папки: {path_in}, {path_out}")

    try:
        if message.document is not None:
            document = message.document
            document_name = message.document.file_name
            logger.info(f"Документ: {document_name}, размер: {document.file_size} bytes")
        elif message.photo is not None:
            document = message.photo[-1]
            document_name = document.file_unique_id + '.jpg'
            logger.info(f"Фото: {document_name}, размер: {document.file_size} bytes")

        filename = '_'.join([str(message.message_id), document_name])
        filepath = f'{path_in}/{filename}'

        logger.debug(f"Скачивание файла в {filepath}")
        await bot.download(document.file_id, destination=filepath)
        logger.info(f"✅ Файл сохранён: {html.code(document_name)}")

    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении файла: {e}", exc_info=True)
    finally:
        logger.info(f"Файл {html.code(document_name)} готов к конвертации")


async def send_file_with_retry(
    message: Message,
    file_path: str,
    caption: str = None,
    max_retries: int = 3
) -> bool:
    """Отправка файла с повторными попытками и логированием"""

    logger.info(f"Начало отправки файла {file_path}")
    logger.debug(f"Параметры: max_retries={max_retries}, caption={caption}")

    for attempt in range(1, max_retries + 1):
        try:
            logger.debug(f"Попытка {attempt}/{max_retries} отправки файла")

            file_to_send = FSInputFile(file_path)
            await message.answer_document(
                document=file_to_send,
                caption=caption
            )

            file_size = os.path.getsize(file_path) / 1024  # в KB
            logger.info(f"✅ Файл успешно отправлен! Размер: {file_size:.2f} KB, попытка: {attempt}")
            return True

        except TelegramRetryAfter as e:
            wait_time = e.retry_after
            logger.warning(f"⏳ Flood control от Telegram. Ждём {wait_time} сек (попытка {attempt}/{max_retries})")
            await asyncio.sleep(wait_time)

        except TelegramNetworkError as e:
            logger.warning(f"🌐 Сетевая ошибка: {e}. Попытка {attempt}/{max_retries}")
            if attempt < max_retries:
                wait_time = 2 ** attempt  # 2, 4, 8 секунд
                logger.debug(f"Повтор через {wait_time} сек")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"❌ Исчерпаны все попытки отправки из-за сетевой ошибки")

        except TelegramBadRequest as e:
            logger.error(f"❌ Bad request ошибка: {e}", exc_info=True)
            # Такую ошибку повторять бесполезно
            break

        except TelegramAPIError as e:
            logger.error(f"❌ Ошибка Telegram API: {e}", exc_info=True)
            if attempt < max_retries:
                await asyncio.sleep(3)
            else:
                logger.error(f"❌ Исчерпаны все попытки отправки")

        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при отправке: {e}", exc_info=True)
            if attempt < max_retries:
                await asyncio.sleep(3)
            else:
                logger.error(f"❌ Исчерпаны все попытки отправки")

    return False


@router.message(F.text.contains('convert'))
async def pdf_converter_handler(message: Message, session: AsyncSession) -> None:
    """Обработчик конвертации PDF"""

    user_id = message.from_user.id
    logger.info(f" === НАЧАЛО КОНВЕРТАЦИИ для пользователя {user_id} ===")
    start_time = asyncio.get_event_loop().time()

    # Даём время на загрузку последних файлов
    logger.debug("Ожидание 5 секунды перед началом конвертации...")
    await asyncio.sleep(5)

    # Проверяем, есть ли пользователь в БД
    logger.debug(f"Поиск пользователя {user_id} в БД")
    user = await crud_user.get_by_telegram_id(
        telegram_id=user_id,
        session=session)

    if not user:
        logger.info(f"Новый пользователь {user_id}. Добавление в БД")
        user_dict = {
                "first_name": message.from_user.first_name,
                "last_name": message.from_user.last_name,
                "username": message.from_user.username,
                "is_premium": message.from_user.is_premium
            }
        await crud_user.create_or_update(
            user_id,
            session,
            **user_dict)
        logger.debug(f"Пользователь {user_id} успешно добавлен")
    else:
        logger.debug(f"Пользователь {user_id} найден в БД")

    path_in, path_out = create_temp_folder(user_id)
    logger.info(f"Временные папки:\n  Вход: {path_in}\n  Выход: {path_out}")

    data = {
        "telegram_id": user_id,
        "is_premium": message.from_user.is_premium,
    }

    # Проверяем наличие файлов для конвертации
    files_in_folder = os.listdir(path_in)
    file_count = len(files_in_folder)
    logger.info(f"Найдено файлов для конвертации: {file_count}")

    if file_count == 0:
        logger.warning(f"Нет файлов для конвертации у пользователя {user_id}")
        await message.answer('❌ Нет загруженных файлов для конвертации')
        return

    # Конвертируем файлы
    try:
        data["number_of_files"] = file_count
        logger.info(f"Начало конвертации {file_count} файлов...")

        result_filename = image_converter_to_pdf(
            path_in,
            path_out,
            message.message_id)

        logger.info(f"✅ Конвертация завершена. Результирующий файл: {result_filename}")

        # Проверяем размер результата
        if os.path.exists(result_filename):
            file_size_kb = os.path.getsize(result_filename) / 1024
            file_size_mb = file_size_kb / 1024
            logger.info(f"Размер PDF: {file_size_kb:.2f} KB ({file_size_mb:.2f} MB)")
            data["file_size"] = os.path.getsize(result_filename)
        else:
            logger.error(f"❌ Файл {result_filename} не создан!")

    except Exception as e:
        logger.error(f"❌ Ошибка при конвертации: {e}", exc_info=True)
        await message.answer('❌ Ошибка при конвертации файлов')
        return

    # Проверяем наличие выходного файла
    files_in_out = os.listdir(path_out)
    logger.debug(f"Файлы в выходной папке: {files_in_out}")

    if len(files_in_out) == 0:
        logger.error(f"❌ Не найден исходящий файл в {path_out}")
        await message.answer('❌ Не найден исходящий файл для отправки')
        return

    # Отправляем результат с повторными попытками
    logger.info(f"Начало отправки результата пользователю {user_id}")

    caption = f"✅ Конвертировано файлов: {file_count}"
    success = await send_file_with_retry(
        message,
        result_filename,
        caption=caption
    )

    # Записываем статистику в БД
    logger.debug("Сохранение данных конвертации в БД")
    await crud_convert.create(
        session=session,
        data=data
    )

    # Очищаем временные файлы
    logger.info("Очистка временных файлов...")

    try:
        await asyncio.sleep(2)  # Даём время на отправку
        delete_files_in_folder(path_in)
        delete_files_in_folder(path_out)
        logger.debug(f"Файлы удалены из {path_in} и {path_out}")

        # Удаляем папки
        common_path = Path(path_in).parent
        Path(path_in).rmdir()
        Path(path_out).rmdir()
        Path(common_path).rmdir()
        logger.debug(f"Временные папки удалены")

    except Exception as e:
        logger.error(f"❌ Ошибка при удалении временных файлов: {e}")

    # Финальный лог
    elapsed_time = asyncio.get_event_loop().time() - start_time
    if success:
        logger.info(f"✨ === КОНВЕРТАЦИЯ УСПЕШНО ЗАВЕРШЕНА для {user_id} за {elapsed_time:.2f}с ===")
    else:
        logger.error(f"💥 === КОНВЕРТАЦИЯ ЗАВЕРШИЛАСЬ ОШИБКОЙ для {user_id} за {elapsed_time:.2f}с ===")