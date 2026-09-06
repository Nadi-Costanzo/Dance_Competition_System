from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config import settings

# Асинхронный движок SQLAlchemy для подключения к базе данных.
async_engine = create_async_engine(settings.database_url)


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
