from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database import enable_sqlite_pragmas
from app.main import app
from app.models.base import Base


@pytest.fixture
def client() -> TestClient:
    """Тестовый HTTP-клиент."""
    return TestClient(app)


@pytest.fixture
def test_db_path(tmp_path: Path) -> Path:
    """Путь к файлу временной базы данных теста."""
    return tmp_path / 'test.db'


@pytest_asyncio.fixture
async def test_engine(test_db_path: Path) -> AsyncGenerator[AsyncEngine, None]:
    """Движок временной базы данных теста."""
    engine = create_async_engine(f'sqlite+aiosqlite:///{test_db_path}')
    enable_sqlite_pragmas(engine)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session_factory(
    test_engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Фабрика сессий к тестовой базе с созданными таблицами."""
    session_factory = async_sessionmaker(
        test_engine,
        expire_on_commit=False,
    )
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return session_factory
