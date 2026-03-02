import img2pdf
import os
import logging
from pathlib import Path
from PIL import Image
import io
from typing import List, Optional

# Настройка логгера для этого модуля
logger = logging.getLogger(__name__)


def compress_image(image_path: str, quality: int = 85, max_size: tuple = None) -> bytes:
    """
    Сжимает изображение и возвращает байты для img2pdf
    
    Args:
        image_path: путь к изображению
        quality: качество JPEG (1-100, 85 - хороший баланс)
        max_size: максимальные размеры (width, height)
    
    Returns:
        bytes: сжатое изображение в формате JPEG
    """
    try:
        with Image.open(image_path) as img:
            # Логируем исходные данные
            logger.debug(f"📸 Оригинал: {image_path}, "
                        f"размер: {img.size}, "
                        f"формат: {img.format}, "
                        f"режим: {img.mode}")
            
            # Конвертируем в RGB если нужно
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Изменяем размер если нужно
            if max_size:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                logger.debug(f"📏 Изменён размер до: {img.size}")
            
            # Сохраняем в буфер с сжатием
            output = io.BytesIO()
            img.save(output, 
                    format='JPEG', 
                    quality=quality,
                    optimize=True,
                    progressive=True)
            
            compressed_size = len(output.getvalue()) / 1024
            logger.debug(f"💾 Сжато: {compressed_size:.1f}KB, качество: {quality}")
            
            return output.getvalue()
            
    except Exception as e:
        logger.error(f"❌ Ошибка сжатия {image_path}: {e}")
        # В случае ошибки читаем оригинал
        with open(image_path, 'rb') as f:
            return f.read()


def get_safe_filename_key(filename: str) -> int:
    """
    Безопасное получение ключа для сортировки из имени файла
    Формат: {message_id}_{original_filename}
    """
    try:
        # Берём первую часть до подчёркивания
        key_part = filename.split('_')[0]
        return int(key_part)
    except (ValueError, IndexError):
        # Если не удалось - кладём в конец
        logger.warning(f"⚠️ Нестандартное имя файла: {filename}")
        return float('inf')


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