import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


def setup_logger(name: str | None = None) -> logging.Logger:
    """Настройка и возврат сконфигурированного логгера."""

    # Создаем папку для логов через pathlib
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Имя логгера
    logger_name = name or __name__
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    # Предотвращаем дублирование обработчиков при повторных вызовах
    if logger.handlers:
        return logger

    # Отключаем передачу логов родительским логгерам (чтобы не дублировать)
    logger.propagate = False

    # Единый форматтер для записей
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 1. Консольный обработчик (уровень INFO+)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. Файловый обработчик с ежедневной ротацией (уровень DEBUG+)
    # Фиксированное имя файла: при ротации появится app.log.2026-08-30 и т.д.
    log_file = log_dir / "app.log"
    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger