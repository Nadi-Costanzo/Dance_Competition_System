from collections.abc import Awaitable, Callable
from pathlib import Path

import httpx
import pytest
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.auth.password import generate_temporary_password
from app.constants import API_PREFIX, FIRST_ADMIN_EMAIL, UserRole
from app.crud.user import get_user_by_email
from app.models.user import User
from app.services.users import ensure_first_admin
from tests.helpers import login_body

TEMPORARY_PASSWORD_LENGTH = 16


@pytest.mark.asyncio
async def test_first_admin_is_created_in_empty_db(
    test_session_factory: async_sessionmaker[AsyncSession],
    tmp_path: Path,
) -> None:
    """Пустая база: администратор создаётся, пароль попадает в файл."""
    password_file = tmp_path / 'admin_password.txt'

    async with test_session_factory() as session:
        password = await ensure_first_admin(session, password_file)

    assert password is not None
    assert len(password) == TEMPORARY_PASSWORD_LENGTH
    assert password_file.read_text(encoding='utf-8') == password

    async with test_session_factory() as session:
        admin = await get_user_by_email(session, FIRST_ADMIN_EMAIL)

    assert admin is not None
    assert admin.role == UserRole.ADMIN
    assert admin.password_hash is not None


@pytest.mark.asyncio
async def test_existing_user_blocks_first_admin(
    test_session_factory: async_sessionmaker[AsyncSession],
    create_user: Callable[..., Awaitable[User]],
    tmp_path: Path,
) -> None:
    """Непустая база: администратор не создаётся, файла нет."""
    await create_user()
    password_file = tmp_path / 'admin_password.txt'

    async with test_session_factory() as session:
        password = await ensure_first_admin(session, password_file)

    assert password is None
    assert not password_file.exists()


@pytest.mark.asyncio
async def test_first_admin_can_log_in_with_generated_password(
    async_client: httpx.AsyncClient,
    test_session_factory: async_sessionmaker[AsyncSession],
    tmp_path: Path,
) -> None:
    """Выданный пароль подходит для входа."""
    async with test_session_factory() as session:
        password = await ensure_first_admin(
            session, tmp_path / 'admin_password.txt'
        )
    assert password is not None, 'Администратор не создан: база пуста.'
    response = await async_client.post(
        f'{API_PREFIX}/auth/login',
        json=login_body(FIRST_ADMIN_EMAIL, password),
    )

    assert response.status_code == status.HTTP_200_OK


def test_temporary_password_is_long_and_random() -> None:
    """Временный пароль: 16 символов, два вызова дают разные значения."""
    first = generate_temporary_password()
    second = generate_temporary_password()

    assert len(first) == TEMPORARY_PASSWORD_LENGTH
    assert first != second
