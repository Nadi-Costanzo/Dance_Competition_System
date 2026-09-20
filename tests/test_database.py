import pytest
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    MetaData,
    Table,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from app.database import initialize_database


@pytest.mark.asyncio
async def test_initialize_database_enables_wal_mode(
    test_engine: AsyncEngine,
) -> None:
    """Проверяет, что initialize_database включает режим WAL."""
    await initialize_database(test_engine)
    async with test_engine.connect() as connection:
        journal_mode = (
            await connection.exec_driver_sql('PRAGMA journal_mode')
        ).scalar_one()
        assert journal_mode.lower() == 'wal'


@pytest.mark.asyncio
async def test_foreign_keys_are_enforced(test_engine: AsyncEngine) -> None:
    """Вставка строки с несуществующим родителем вызывает IntegrityError."""
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
    async with test_engine.begin() as connection:
        await connection.run_sync(metadata.create_all)

    with pytest.raises(IntegrityError):
        async with test_engine.begin() as connection:
            await connection.execute(
                children.insert().values(parent_id=999),
            )
