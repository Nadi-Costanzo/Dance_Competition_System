import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import FIRST_ADMIN_EMAIL, UserRole
from app.models.user import User


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Возвращает пользователя с указанным адресом или None."""
    result = await session.scalars(select(User).where(User.email == email))
    return result.first()


async def increment_token_version(
    session: AsyncSession, user_id: uuid.UUID
) -> int | None:
    """Атомарно увеличивает `token_version` пользователя.

    Результат:
        - Новое значение `token_version`;
        - None — пользователя с указанным id нет.
    Транзакцию завершает вызывающий слой.
    """
    stmt = (
        update(User)
        .where(User.id == user_id)
        # Значение — выражение, а не число: инкремент выполняет база,
        # поэтому параллельные вызовы не теряют приращение.
        .values(token_version=User.token_version + 1)
        # Пустой результат означает «записи нет»: отдельный SELECT
        # перед обновлением не нужен.
        .returning(User.token_version)
    )
    new_version: int | None = await session.scalar(stmt)
    return new_version


async def set_password_and_increment_version(
    session: AsyncSession, user_id: uuid.UUID, new_hash: str
) -> int | None:
    """Атомарно записывает `password_hash` и увеличивает `token_version`.

    Результат:
        - Новое значение `token_version`;
        - None — пользователя с указанным id нет.
    Транзакцию завершает вызывающий слой.
    """
    stmt = (
        update(User)
        .where(User.id == user_id)
        .values(
            password_hash=new_hash,
            token_version=User.token_version + 1,
        )
        .returning(User.token_version)
    )
    new_version: int | None = await session.scalar(stmt)
    return new_version


async def has_users(session: AsyncSession) -> bool:
    """Возвращает True, если в БД есть хотя бы один пользователь."""
    return await session.scalar(select(User.id).limit(1)) is not None


async def add_first_admin(session: AsyncSession, password_hash: str) -> User:
    """Добавляет запись первого администратора.

    Адрес, ФИО и роль фиксированы, варьируется только хеш пароля.
    Проверку пустой базы и фиксацию транзакции выполняет вызывающий слой.
    """
    admin = User(
        email=FIRST_ADMIN_EMAIL,
        password_hash=password_hash,
        surname='Admin',
        name='Admin',
        role=UserRole.ADMIN,
    )
    session.add(admin)
    await session.flush()
    return admin
