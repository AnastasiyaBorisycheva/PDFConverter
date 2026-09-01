import asyncio
import io
import logging
import os
from pathlib import Path
from typing import List, Optional

import img2pdf
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)


def compress_image(image_path: str | Path, quality: int = 100, max_size: tuple = None) -> bytes:
    """
    Сжимает изображение и возвращает байты для img2pdf.
    Учитывает EXIF-поворот фото со смартфонов.
    """
    try:
        with Image.open(image_path) as img:
            # Корректируем ориентацию по EXIF (чтобы фото не получались перевернутыми)
            img = ImageOps.exif_transpose(img)

            logger.debug(
                f"Оригинал: {image_path}, размер: {img.size}, "
                f"формат: {img.format}, режим: {img.mode}"
            )

            # Конвертируем в RGB если нужно (для избавлением от альфа-канала)
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")

            # Изменяем размер пропорционально
            if max_size:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                logger.debug(f"Изменён размер до: {img.size}")

            # Сохраняем в буфер с сжатием
            output = io.BytesIO()
            img.save(
                output,
                format="JPEG",
                quality=quality,
                optimize=True,
                progressive=True,
            )

            compressed_bytes = output.getvalue()
            compressed_size = len(compressed_bytes) / 1024
            logger.debug(f"Сжато: {compressed_size:.1f}KB, качество: {quality}")

            return compressed_bytes

    except Exception as e:
        logger.error(f"❌ Ошибка сжатия {image_path}: {e}")
        # В случае ошибки читаем оригинальный файл
        with open(image_path, "rb") as f:
            return f.read()


def get_safe_filename_key(filename: str) -> float:
    """Безопасное получение ключа для сортировки из имени файла."""
    try:
        key_part = filename.split("_")[0]
        return float(key_part)
    except (ValueError, IndexError):
        logger.warning(f"Нестандартное имя файла: {filename}")
        return float("inf")


def image_converter_to_pdf(
    input_directory: str,
    output_directory: str,
    message_id: int,
    quality: int = 75,  # По умолчанию 75% - хороший баланс
    max_width: Optional[int] = 1200,  # Ограничиваем ширину
    max_height: Optional[int] = 1800,  # Ограничиваем высоту
    allowed_extensions: tuple = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff')
) -> Optional[str]:
    """
    Конвертирует изображения в PDF со сжатием
    
    Args:
        input_directory: папка с исходными изображениями
        output_directory: папка для результата
        message_id: ID сообщения для имени файла
        quality: качество JPEG (1-100, меньше = сильнее сжатие)
        max_width: максимальная ширина (None = без изменений)
        max_height: максимальная высота (None = без изменений)
        allowed_extensions: разрешённые расширения
    
    Returns:
        str: путь к PDF файлу или None при ошибке
    """
    
    logger.info(f"🔄 Начало конвертации в PDF")
    logger.info(f"📁 Входная папка: {input_directory}")
    logger.info(f"📁 Выходная папка: {output_directory}")
    
    # Проверяем входную папку
    if not os.path.exists(input_directory):
        logger.error(f"❌ Папка не существует: {input_directory}")
        return None
    
    # Собираем все изображения
    image_files = []
    all_files = os.listdir(input_directory)
    logger.info(f"📊 Всего файлов в папке: {len(all_files)}")
    
    for fname in all_files:
        file_path = os.path.join(input_directory, fname)
        
        # Пропускаем папки
        if os.path.isdir(file_path):
            logger.debug(f"📁 Пропущена папка: {fname}")
            continue
        
        # Проверяем расширение
        if not fname.lower().endswith(allowed_extensions):
            logger.debug(f"⏭️ Пропущен неподдерживаемый формат: {fname}")
            continue
        
        # Проверяем размер файла
        file_size = os.path.getsize(file_path) / 1024  # KB
        if file_size > 50 * 1024:  # > 50MB
            logger.warning(f"⚠️ Слишком большой файл ({file_size:.1f}KB): {fname}")
            continue
        
        image_files.append(file_path)
        logger.debug(f"✅ Добавлен файл: {fname} ({file_size:.1f}KB)")
    
    # Проверяем, есть ли изображения
    if not image_files:
        logger.error("❌ Нет подходящих изображений для конвертации")
        return None
    
    logger.info(f"🖼️ Найдено изображений для конвертации: {len(image_files)}")
    
    # Сортируем файлы
    try:
        image_files.sort(key=lambda x: get_safe_filename_key(os.path.basename(x)))
        logger.debug("✅ Файлы отсортированы")
    except Exception as e:
        logger.warning(f"⚠️ Ошибка сортировки: {e}, используем порядок файловой системы")
    
    # Сжимаем и конвертируем изображения
    compressed_images = []
    max_size = (max_width, max_height) if max_width and max_height else None
    
    for i, img_path in enumerate(image_files, 1):
        logger.info(f"🔄 Обработка {i}/{len(image_files)}: {os.path.basename(img_path)}")
        
        # Сжимаем изображение
        img_data = compress_image(
            img_path, 
            quality=quality,
            max_size=max_size
        )
        compressed_images.append(img_data)
        
        # Логируем прогресс
        if i % 5 == 0:
            logger.info(f"📊 Прогресс: {i}/{len(image_files)}")
    
    # Создаём PDF
    output_filename = f"result_{message_id}.pdf"
    output_path = os.path.join(output_directory, output_filename)
    
    try:
        logger.info(f"📄 Создание PDF: {output_path}")
        
        # Конвертируем в PDF
        pdf_bytes = img2pdf.convert(
            compressed_images,
            title=f"Converted by PDFConverter",
            author="Telegram Bot",
            creator="PDFConverter Bot"
        )
        
        # Сохраняем PDF
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        
        # Проверяем результат
        if os.path.exists(output_path):
            pdf_size = os.path.getsize(output_path) / 1024
            logger.info(f"✅ PDF создан успешно!")
            logger.info(f"📊 Размер PDF: {pdf_size:.1f}KB")
            logger.info(f"📄 Страниц: {len(compressed_images)}")
            
            # Сравниваем с оригиналом (примерно)
            original_size = sum(os.path.getsize(f) for f in image_files) / 1024
            compression_ratio = (pdf_size / original_size * 100) if original_size > 0 else 0
            logger.info(f"💾 Сжатие: {original_size:.1f}KB → {pdf_size:.1f}KB "
                       f"({compression_ratio:.1f}%)")
            
            return output_path
        else:
            logger.error("❌ PDF файл не создан")
            return None
            
    except img2pdf.AlphaChannelError as e:
        logger.error(f"❌ Ошибка альфа-канала: {e}")
        return None
    except img2pdf.PdfTooLargeError as e:
        logger.error(f"❌ PDF слишком большой: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка при создании PDF: {e}", exc_info=True)
        return None


def get_pdf_preview_info(pdf_path: str) -> dict:
    """Получает информацию о PDF без его открытия"""
    info = {
        "size_kb": 0,
        "exists": False,
        "filename": os.path.basename(pdf_path) if pdf_path else None
    }
    
    if pdf_path and os.path.exists(pdf_path):
        info["exists"] = True
        info["size_kb"] = os.path.getsize(pdf_path) / 1024
    
    return info


def _sync_image_converter_to_pdf(
    input_directory: str | Path = "IN",
    output_directory: str | Path = "OUT",
    message_id: int = 0,
    quality: int = 100,
    max_width: Optional[int] = 1200,
    max_height: Optional[int] = 1800,
    allowed_extensions: tuple = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"),
) -> Optional[str]:
    """Синхронная функция подготовки и сборки PDF."""
    input_path = Path(input_directory)
    output_path_dir = Path(output_directory)

    if not input_path.exists():
        logger.error(f"❌ Папка не существует: {input_path}")
        return None

    # Собираем все поддерживаемые изображения
    image_files = []
    for entry in input_path.iterdir():
        if entry.is_file() and entry.suffix.lower() in allowed_extensions:
            file_size_kb = entry.stat().st_size / 1024
            if file_size_kb > 50 * 1024:  # > 50MB
                logger.warning(f"Слишком большой файл ({file_size_kb:.1f}KB): {entry.name}")
                continue
            image_files.append(entry)

    if not image_files:
        logger.error("Нет подходящих изображений для конвертации")
        return None

    # Сортируем файлы по ключу
    image_files.sort(key=lambda x: get_safe_filename_key(x.name))

    # Сжимаем изображения
    compressed_images = []
    max_size = (max_width, max_height) if max_width and max_height else None

    for i, img_path in enumerate(image_files, 1):
        logger.info(f"Обработка {i}/{len(image_files)}: {img_path.name}")
        img_data = compress_image(img_path, quality=quality, max_size=max_size)
        compressed_images.append(img_data)

    output_file_path = output_path_dir / f"result_{message_id}.pdf"

    try:
        logger.info(f"Создание PDF: {output_file_path}")
        
        pdf_bytes = img2pdf.convert(
            compressed_images,
            title="Converted by PDFConverter",
            author="Telegram Bot",
            creator="PDFConverter Bot",
        )

        with open(output_file_path, "wb") as f:
            f.write(pdf_bytes)

        if output_file_path.exists():
            pdf_size = output_file_path.stat().st_size / 1024
            logger.info(f"PDF создан успешно! Размер: {pdf_size:.1f}KB")
            return str(output_file_path)
        
        return None

    except img2pdf.AlphaChannelError as e:
        logger.error(f"Ошибка альфа-канала: {e}")
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при создании PDF: {e}", exc_info=True)
        return None


async def convert_images_to_pdf(
    input_directory: str | Path,
    output_directory: str | Path,
    message_id: int,
    quality: int = 75,
    max_width: Optional[int] = 1200,
    max_height: Optional[int] = 1800,
) -> Optional[str]:
    """
    Асинхронный интерфейс для конвертации изображений в PDF.
    Безопасно запускает блокирующую сборку в отдельном потоке execution pool.
    """
    return await asyncio.to_thread(
        _sync_image_converter_to_pdf,
        input_directory=input_directory,
        output_directory=output_directory,
        message_id=message_id,
        quality=quality,
        max_width=max_width,
        max_height=max_height,
    )