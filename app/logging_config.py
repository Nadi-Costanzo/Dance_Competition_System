import logging
from logging.handlers import RotatingFileHandler

from app.config import settings
from app.constants import (
    LOG_BACKUP_COUNT,
    LOG_DATEFMT,
    LOG_FILE_PATH,
    LOG_FORMAT,
    LOG_MAX_BYTES,
)


def _resolve_log_level(level_name: str) -> str:
    """Проверяет корректность имени логирования.

    ValueError для неизвестного имени.
    """
    upper = level_name.upper()
    if upper not in logging.getLevelNamesMapping():  # dict[str, int]
        raise ValueError(f'Неизвестный уровень логирования: {level_name!r}')
    return upper


_LOG_LEVEL = _resolve_log_level(settings.log_level)
_FORMATTER = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATEFMT)

# Единственные хендлеры на весь процесс — создаются один раз при импорте.
_CONSOLE_HANDLER = logging.StreamHandler()
_CONSOLE_HANDLER.setFormatter(_FORMATTER)

LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

_FILE_HANDLER = RotatingFileHandler(
    LOG_FILE_PATH,
    maxBytes=LOG_MAX_BYTES,
    backupCount=LOG_BACKUP_COUNT,
    encoding='utf-8',
)
_FILE_HANDLER.setFormatter(_FORMATTER)


def _configure_logger(logger: logging.Logger, log_level: str) -> None:
    """Готовит логгер: уровень + общие (модульные) хендлеры."""
    logger.setLevel(log_level)
    logger.propagate = False
    logger.addHandler(_CONSOLE_HANDLER)
    logger.addHandler(_FILE_HANDLER)


def get_logger(name: str) -> logging.Logger:
    """Возвращает отконфигурированный логгер."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        _configure_logger(logger, log_level=_LOG_LEVEL)
    return logger


def setup_logging() -> None:
    """Настройка корневого логирования для всего приложения."""
    for uvicorn_logger_name in ('uvicorn', 'uvicorn.error', 'uvicorn.access'):
        uvicorn_logger = logging.getLogger(uvicorn_logger_name)
        uvicorn_logger.handlers = []
        _configure_logger(uvicorn_logger, log_level=_LOG_LEVEL)
