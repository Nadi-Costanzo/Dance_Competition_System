from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config import settings


def _apply_sqlite_pragmas(
    dbapi_connection: Any, _connection_record: Any
) -> None:
    """Применяет обязательные PRAGMA уровня соединения SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute('PRAGMA foreign_keys=ON')
    cursor.execute('PRAGMA busy_timeout=5000')
    cursor.close()


def enable_sqlite_pragmas(engine: AsyncEngine) -> None:
    """Регистрирует обработчик обязательных PRAGMA на соединениях движка.

    Args:
        engine: движок, чьи соединения должны включать foreign_keys
            и busy_timeout (приложение, Alembic, тесты).
    """
    event.listen(engine.sync_engine, 'connect', _apply_sqlite_pragmas)


# Асинхронный движок SQLAlchemy для подключения к базе данных.
async_engine = create_async_engine(settings.database_url)
enable_sqlite_pragmas(async_engine)


async def initialize_database(database_engine: AsyncEngine) -> None:
    """Инициализирует подключение к БД и включает режим WAL."""
    async with database_engine.connect() as connection:
        journal_mode = (
            await connection.exec_driver_sql('PRAGMA journal_mode=WAL')
        ).scalar_one()
        if journal_mode.lower() != 'wal':
            raise RuntimeError(
                'Не удалось включить режим WAL:'
                f' получен режим {journal_mode!r}.',
            )


async def check_database_connection(database_engine: AsyncEngine) -> None:
    """Проверяет подключение к БД."""
    async with database_engine.connect() as connection:
        await connection.exec_driver_sql('SELECT 1')
