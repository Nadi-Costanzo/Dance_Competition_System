from enum import StrEnum

NAMING_CONVENTION = {
    'ix': 'ix_%(column_0_label)s',
    'uq': 'uq_%(table_name)s_%(column_0_N_name)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s',
}
"""Словарь с соглашениями для автогенерации имен"""

API_PREFIX = '/api/v1'
"""Общий базовый префикс URL"""

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

LOG_FORMAT = '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
"""Формат логирования."""

LOG_MAX_BYTES = 30 * 1024 * 1024
"""Максимальный размер файла логов в байтах."""

LIBRARY_LOGGER_NAMES = ('sqlalchemy', 'httpx', 'httpcore')
"""Логгеры, порог логирования которых поднимается минимум до WARNING."""

SYSTEM_LOGGER_NAMES = ('uvicorn', 'uvicorn.error', 'uvicorn.access')
"""Логгеры uvicorn, порог логирования которых задается в settings."""

# USERS
EMAIL_MAX_LENGTH: int = 255
"""Максимальная длина email."""

PASSWORD_HASH_MAX_LENGTH: int = 255
"""Максимальная длина хеша пароля."""

FIO_MAX_LENGTH: int = 30
"""Максимальная длина полей ФИО."""

ROLE_MAX_LENGTH: int = 10
"""Используется в моделях User и ClubMembership."""


class UserRole(StrEnum):
    """Справочник ролей пользователей."""

    ADMIN = 'admin'
    USER = 'user'


JUDGE_CATEGORY_MAX_LENGTH: int = 20
"""Максимальная длина кода судейской категории."""


class JudgeCategory(StrEnum):
    """Квалификационные категории спортивных судей.

    Отсутствие категории — NULL в users.judge_category:
    отдельного элемента перечисления для этого не предусмотрено.
    Поле справочное: на назначение судей не влияет,
    решение принимается по is_certified_judge.

    MASS_SPORT - все судьи по массовому спорту (1-5 категорий).
    """

    MASS_SPORT = 'mass_sport'
    YOUTH = 'youth'
    THIRD = 'third'
    SECOND = 'second'
    FIRST = 'first'
    ALL_RUSSIAN = 'all_russian'


JUDGE_CATEGORY_LABELS: dict[JudgeCategory, str] = {
    JudgeCategory.MASS_SPORT: 'судья соревнований по массовому спорту',
    JudgeCategory.YOUTH: 'юный спортивный судья',
    JudgeCategory.THIRD: 'третья категория',
    JudgeCategory.SECOND: 'вторая категория',
    JudgeCategory.FIRST: 'первая категория',
    JudgeCategory.ALL_RUSSIAN: 'всероссийская категория',
}


SYNC_ORIGIN_MAX_LENGTH: int = 10
"""Максимальная длина кода "источник синхонизации"."""


class SyncOrigin(StrEnum):
    """Источник синхронизации. Служит для процедуры импорта пользователя."""

    LOCAL = 'local'
    CLOUD = 'cloud'


# JWT и аутентификация пользователей

ACCESS_TOKEN_LIFETIME_HOURS = 12
"""время жизни токена (часы)."""

JWT_ALGORITHM = 'HS256'
