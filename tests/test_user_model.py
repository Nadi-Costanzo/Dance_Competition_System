import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from app.constants import UserRole
from app.models.user import User


@pytest.mark.asyncio
async def test_users_have_unique_email(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Проверяет уникальность значения поля users.email."""
    async with test_session_factory() as session:
        session.add(
            User(
                email='user_1@test.ru',
                surname='Пупкин',
                name='Ваня',
            )
        )
        await session.commit()

    with pytest.raises(
        IntegrityError,
        match=r'UNIQUE constraint failed: users\.email',
    ):
        async with test_session_factory() as session:
            session.add(
                User(
                    email='user_1@test.ru',
                    surname='Пупкин',
                    name='Ваня',
                )
            )
            await session.commit()


@pytest.mark.asyncio
async def test_users_role(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Проверяет невозможность присвоить пользователю несуществующую роль."""
    with pytest.raises(
        IntegrityError,
        match=r'CHECK constraint failed: ck_users_valid_role',
    ):
        async with test_session_factory() as session:
            session.add(
                User(
                    email='user_1@test.ru',
                    surname='Пупкин',
                    name='Ваня',
                    role='manager',
                )
            )
            await session.commit()


@pytest.mark.asyncio
async def test_users_have_default_values(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Проверяет корректность дефолтных значений."""
    async with test_session_factory() as session:
        user = User(
            email='user_1@test.ru',
            surname='Пупкин',
            name='Ваня',
        )
        session.add(user)
        await session.flush()
        assert user.role == UserRole.USER
        assert user.token_version == 0
        assert user.is_certified_judge is False
        assert isinstance(user.id, uuid.UUID)


@pytest.mark.asyncio
async def test_user_repr_hides_password_hash(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Проверяет отсутствие в repr поля password_hash."""
    async with test_session_factory() as session:
        user = User(
            email='user_1@test.ru',
            surname='Пупкин',
            name='Ваня',
            password_hash='secret-hash-value',
        )
        session.add(user)
        await session.flush()
        user_repr = repr(user)
        assert 'secret-hash-value' not in user_repr
        assert 'user_1@test.ru' in user_repr
        assert str(user.id) in user_repr
