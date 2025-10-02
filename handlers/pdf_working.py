import os
from pathlib import Path
from time import sleep

from aiogram import Bot, F, Router, html
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
    """Здесь будет только сохранение файлов в темповую папку по айди юзера."""

    path_in, path_out = create_temp_folder(message.from_user.id)

    try:
        if message.document is not None:
            document = message.document
            document_name = message.document.file_name
        elif message.photo is not None:
            document = message.photo[-1]
            document_name = document.file_unique_id + '.jpg'

        filename = '_'.join([str(message.message_id), document_name])
        filepath = f'{path_in}/{filename}'
        await bot.download(document.file_id, destination=filepath)
    except Exception as e:
        logger.error(f"Exception came: {e}")
        print(e)
    finally:
        logger.info(f"File {html.code(document_name)} saved for conversion.")


@router.message(F.text.contains('convert'))
async def pdf_converter_handler(message: Message, session: AsyncSession) -> None:

    sleep(2)

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

    path_in, path_out = create_temp_folder(message.from_user.id)
    data = {
        "telegram_id": message.from_user.id,
        "is_premium": message.from_user.is_premium,
    }

    try:
        if len(os.listdir(path_in)) == 0:
            await message.answer('Нет загруженных файлов для конвертации')
        else:
            number_of_files = len(os.listdir(path_in))
            data["number_of_files"] = number_of_files
            result_filename = image_converter_to_pdf(
                path_in,
                path_out,
                message.message_id)
    except Exception as e:
        logger.error(f"Exception came: {e}")

    if len(os.listdir(path_out)) == 0:
        await message.answer('Не найден исходящий файл для отправки')
    else:
        try:
            file_to_send = FSInputFile(result_filename)
            data["file_size"] = os.stat(result_filename).st_size
            await message.answer_document(file_to_send)
        except Exception as e:
            logger.error(f"Error while sending a file: {e}")
        finally:
            await crud_convert.create(
                session=session,
                data=data
            )
            sleep(2)
            delete_files_in_folder(path_in)
            delete_files_in_folder(path_out)
            common_path = Path(path_in).parent
            # Remove the temporary folders after sending the file
            Path(path_in).rmdir()
            Path(path_out).rmdir()
            Path(common_path).rmdir()  # Remove the common temp folder
