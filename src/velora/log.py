from __future__ import annotations

import logging
import os
import sys
import threading
from logging.handlers import RotatingFileHandler

_LOGGER_NAME = "velora"
_configured = False


def configure_logging(data_dir="data"):
    """Configure durable application logging.

    Everything at DEBUG+ is written to data/velora.log with rotation.
    Unhandled exceptions from the main and worker threads are logged with
    tracebacks so a runtime failure can be diagnosed from the log alone.
    """
    global _configured
    os.makedirs(data_dir, exist_ok=True)
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if not _configured:
        file_handler = RotatingFileHandler(
            os.path.join(data_dir, "velora.log"),
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s.%(msecs)03d %(levelname)s "
            "[%(process)d:%(threadName)s] %(name)s.%(funcName)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(formatter)
        logger.addHandler(console)

        def excepthook(exc_type, exc_value, exc_tb):
            if exc_type is KeyboardInterrupt:
                sys.__excepthook__(exc_type, exc_value, exc_tb)
                return
            logger.critical("UNHANDLED EXCEPTION", exc_info=(exc_type, exc_value, exc_tb))

        def thread_excepthook(args):
            logger.critical(
                "UNHANDLED THREAD EXCEPTION in %s",
                args.thread.name if args.thread else "<unknown>",
                exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
            )

        sys.excepthook = excepthook
        threading.excepthook = thread_excepthook
        _configured = True

    logger.info("logging initialized: file=%s level=DEBUG", os.path.join(data_dir, "velora.log"))
    return logger


def get_logger(name="velora"):
    return logging.getLogger(name if name.startswith("velora") else f"velora.{name}")
