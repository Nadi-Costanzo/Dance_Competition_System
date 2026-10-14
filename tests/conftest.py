from collections.abc import AsyncGenerator, Awaitable, Callable, Generator
from pathlib import Path

import httpx
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.auth.password import hash_password
from app.database import enable_sqlite_pragmas, get_async_session
from app.main import app
from app.models.base import Base
from app.models.user import User
from tests.constants import TEST_EMAIL, TEST_ERROR_ROUTE, TEST_PASSWORD


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


@pytest.fixture
def client_raising() -> Generator[Callable[..., TestClient], None, None]:
    """Отдаёт фабрику клиента с маршрутом, возбуждающим заданное исключение."""
    original = app.router.routes.copy()

    def make_client(
        error: Exception, raise_server_exceptions: bool = True
    ) -> TestClient:
        @app.get(TEST_ERROR_ROUTE)
        async def _raise_error() -> None:
            raise error

        return TestClient(
            app,
            raise_server_exceptions=raise_server_exceptions,
        )

    yield make_client
    app.router.routes[:] = original


@pytest_asyncio.fixture
async def async_client(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Клиент к приложению с тестовой базой данных.

    Асинхронный (httpx.AsyncClient + ASGITransport),
    фикстуры и движок тестовой базы работают в цикле теста.
    """

    async def override_session() -> AsyncGenerator[AsyncSession, None]:
        """Открывает сессию к тестовой базе.

        Переопределяет зависимость get_async_session для тестов.
        """
        async with test_session_factory() as session:
            yield session

    # Без подмены запросы ушли бы в рабочую базу из .env.
    app.dependency_overrides[get_async_session] = override_session
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url='http://test'
    ) as client:
        yield client
    # Снимаем подмену: app живёт весь прогон, иначе она
    # досталась бы следующим тестам.
    app.dependency_overrides.pop(get_async_session, None)


@pytest_asyncio.fixture
async def create_user(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[Callable[..., Awaitable[User]], None]:
    """Фабрика пользователей в тестовой базе.

    Возвращает фабрику со своими аргументами: email, password, is_active.
    - password=None создаёт запись без хеша (ACCOUNT_NOT_ACTIVATED)
    - is_active=False — отключённую (ACCOUNT_DISABLED).
    """

    async def user_factory(
        email: str = TEST_EMAIL,
        password: str | None = TEST_PASSWORD,
        is_active: bool = True,
    ) -> User:
        """Создаёт пользователя в тестовой базе.

        Args:
            email: адрес пользователя.
            password: открытый пароль; None — запись без хеша.
            is_active: False — отключённая запись.
        """
        password_hash = (
            None if password is None else await hash_password(password)
        )
        user = User(
            email=email,
            password_hash=password_hash,
            name='Пользователь',
            surname='Тестовый',
            is_active=is_active,
        )

        async with test_session_factory() as session:
            session.add(user)
            await session.commit()
        return user

    yield user_factory
