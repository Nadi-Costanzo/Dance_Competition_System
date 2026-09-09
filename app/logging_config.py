import logging
from logging.handlers import RotatingFileHandler

from app.config import settings
from app.constants import (
    LOG_BACKUP_COUNT,
    LOG_DATEFMT,
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
_handlers: list[logging.Handler] | None = None


def _get_handlers() -> list[logging.Handler]:
    """Создает и возвращает общие хендлеры.

    Создаются только при первом вызове и сохраняются в глобальную переменную.
    """
    global _handlers
    if _handlers is None:
        # первое обращение:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(_FORMATTER)
        log_file_path = (settings.log_dir / 'app.log').resolve()
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8',
        )
        file_handler.setFormatter(_FORMATTER)
        _handlers = [console_handler, file_handler]
    return _handlers


def _configure_logger(logger: logging.Logger, log_level: str) -> None:
    """Готовит логгер: уровень + общие хендлеры."""
    logger.setLevel(log_level)
    logger.propagate = False
    for handler in _get_handlers():
        logger.addHandler(handler)


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
