"""Structured logging configuration for CampusPulse."""

import logging
import sys
from .config import get_settings


def setup_logging() -> logging.Logger:
    """Configure and return the root application logger."""
    settings = get_settings()
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    log_format = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    logger = logging.getLogger("campuspulse")
    logger.setLevel(log_level)
    logger.info(f"Logging initialized at level: {settings.LOG_LEVEL} (env={settings.APP_ENV})")
    return logger


logger = logging.getLogger("campuspulse")
