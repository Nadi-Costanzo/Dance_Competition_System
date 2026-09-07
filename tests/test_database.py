from pathlib import Path

import pytest
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    MetaData,
    Table,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine

from app.database import enable_sqlite_pragmas, initialize_database


@pytest.mark.asyncio
async def test_initialize_database_enables_wal_mode(tmp_path: Path) -> None:
    """Проверяет, что initialize_database включает режим WAL."""
    test_database_path = tmp_path / 'test.db'
    test_database_url = f'sqlite+aiosqlite:///{test_database_path}'
    test_engine = create_async_engine(test_database_url)
    try:
        await initialize_database(test_engine)
        async with test_engine.connect() as connection:
            journal_mode = (
                await connection.exec_driver_sql('PRAGMA journal_mode')
            ).scalar_one()
            assert journal_mode.lower() == 'wal'
    finally:
        await test_engine.dispose()


@pytest.mark.asyncio
async def test_foreign_keys_are_enforced(tmp_path: Path) -> None:
    """Вставка строки с несуществующим родителем вызывает IntegrityError."""
    test_database_path = tmp_path / 'test.db'
    test_database_url = f'sqlite+aiosqlite:///{test_database_path}'
    test_engine = create_async_engine(test_database_url)
    enable_sqlite_pragmas(test_engine)

    metadata = MetaData()
    Table(
        'parents',
        metadata,
        Column('id', Integer, primary_key=True),
    )
    children = Table(
        'children',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('parent_id', Integer, ForeignKey('parents.id'), nullable=False),
    )
    try:
        async with test_engine.begin() as connection:
            await connection.run_sync(metadata.create_all)

        with pytest.raises(IntegrityError):
            async with test_engine.begin() as connection:
                await connection.execute(
                    children.insert().values(parent_id=999),
                )
    finally:
        await test_engine.dispose()
