# logger.py

import os
import logging

from datetime import datetime


def configure_logger():

    os.makedirs(
        "logs",
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    log_file = (
        f"logs/{timestamp}.log"
    )

    logger = logging.getLogger(
        "canvas_migrator"
    )

    logger.setLevel(
        logging.INFO
    )

    file_handler = logging.FileHandler(
        log_file,
        encoding="utf-8"
    )

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler.setFormatter(
        formatter
    )

    logger.addHandler(
        file_handler
    )

    return logger