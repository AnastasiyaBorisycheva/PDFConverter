import logging
import sys
from pathlib import Path


def setup_logger(name="my_app"):

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(Path("logs/app.log"), mode="a")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
