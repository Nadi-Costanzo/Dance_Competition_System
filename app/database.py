from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config import settings

async_engine = create_async_engine(settings.database_url)


async def initialize_database(database_engine: AsyncEngine) -> None:
    """Инициализирует подключение к БД и включает режим WAL."""
    async with database_engine.connect() as connection:
        journal_mode = (
            await connection.exec_driver_sql("PRAGMA journal_mode=WAL")
        ).scalar_one()
        if journal_mode.lower() != "wal":
            raise RuntimeError(
                f"Не удалось включить режим WAL: получен режим {journal_mode!r}.",
            )
