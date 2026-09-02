from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from app.database import initialize_database


@pytest.mark.asyncio
async def test_initialize_database_enables_wal_mode(tmp_path: Path) -> None:
    """Проверяет, что initialize_database включает режим WAL."""
    test_database_path = tmp_path / "test.db"
    test_database_url = f"sqlite+aiosqlite:///{test_database_path}"
    test_engine = create_async_engine(test_database_url)
    try:
        await initialize_database(test_engine)
        async with test_engine.connect() as connection:
            journal_mode = (
                await connection.exec_driver_sql("PRAGMA journal_mode")
            ).scalar_one()
            assert journal_mode.lower() == "wal"
    finally:
        await test_engine.dispose()
