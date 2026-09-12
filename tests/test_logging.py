import logging

from app.constants import LIBRARY_LOGGER_NAMES
from app.logging_config import setup_logging


def test_library_loggers_are_not_below_warning() -> None:
    """Проверяет, что уровень логирования сторонних библиотек >= WARNING."""
    setup_logging()
    for name in LIBRARY_LOGGER_NAMES:
        assert logging.getLogger(name).level >= logging.WARNING
