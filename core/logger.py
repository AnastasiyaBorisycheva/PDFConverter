import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler


def setup_logger(name=None):
    """Настройка и возврат логгера"""

    # Создаем папку для логов, если её нет
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Имя логгера
    if name is None:
        name = __name__

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Проверяем, нет ли уже обработчиков у логгера
    if logger.handlers:
        return logger

    # Форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%d.%m.%Y %H:%M:%S'
    )

    # Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Обработчик для файла с ротацией
    log_file = os.path.join(log_dir, f'app_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when='D',
        backupCount=7,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)

    return logger
