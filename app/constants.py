from pathlib import Path

NAMING_CONVENTION = {
    'ix': 'ix_%(column_0_label)s',
    'uq': 'uq_%(table_name)s_%(column_0_N_name)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s',
}
"""Словарь с соглашениями для автогенерации имен"""

DB_CHECK_TIMEOUT_S = 2.0
"""Время ожидания проверки доступности базы данных в секундах."""

# Диагностические тексты для /health (поле detail). Не машинные коды.
DB_DETAIL_TIMEOUT = (
    f'База данных не отвечает в течение {DB_CHECK_TIMEOUT_S} с.'
)
DB_DETAIL_LOCKED = 'База данных заблокирована другим процессом.'
DB_DETAIL_UNAVAILABLE = 'База данных недоступна.'


# Конфигурация логирования
LOG_BACKUP_COUNT = 3
"""Максимальное число хранимых старых файлов логирования."""

LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'
"""Формат даты и времени для логгера."""

LOG_FILE_PATH = Path('logs/app.log')
"""Путь к логам."""

LOG_FORMAT = '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
"""Формат логирования."""

LOG_MAX_BYTES = 30 * 1024 * 1024
"""Максимальный размер файла логов в байтах."""
