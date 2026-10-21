import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.password import hash_password, verify_password
from app.constants import (
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    WEAK_PASSWORDS,
)
from app.crud.user import get_user_by_email, increment_token_version
from app.error_codes import ErrorCode
from app.exceptions import BusinessError
from app.models.user import User


def _is_monotonic_sequence(password: str) -> bool:
    """True, если все соседние символы идут с шагом +1 или -1."""
    diffs = {
        ord(b) - ord(a)
        for a, b in zip(
            password,
            password[1:],
            strict=False,
        )
    }
    return diffs in ({1}, {-1})


async def _require_valid_password(
    password: str, password_hash: str | None
) -> None:
    """Подтверждает пароль учётной записи.

    Отказ:
    ACCOUNT_NOT_ACTIVATED, если пароль не задан;
    INVALID_CREDENTIALS, если переданный пароль не совпадает.
    """
    if password_hash is None:
        raise BusinessError(ErrorCode.ACCOUNT_NOT_ACTIVATED)
    if not await verify_password(password, password_hash):
        raise BusinessError(ErrorCode.INVALID_CREDENTIALS)


async def authenticate(
    session: AsyncSession, email: str, password: str
) -> User:
    """Проверяет email и пароль, возвращает пользователя.

    При отказе возбуждает BusinessError.
    """
    user = await get_user_by_email(session, email)
    if user is None:
        raise BusinessError(ErrorCode.INVALID_CREDENTIALS)
    await _require_valid_password(password, user.password_hash)
    if not user.is_active:
        raise BusinessError(ErrorCode.ACCOUNT_DISABLED)
    return user


def validate_password_policy(
    new_password: str, user: User, current_password: str
) -> None:
    """Проверяет пароль, при нарушении возбуждает BusinessError."""
    if not (PASSWORD_MIN_LENGTH <= len(new_password) <= PASSWORD_MAX_LENGTH):
        raise BusinessError(
            ErrorCode.PASSWORD_POLICY_VIOLATION,
            (
                'Пароль должен содержать от '
                f'{PASSWORD_MIN_LENGTH} до {PASSWORD_MAX_LENGTH} символов.'
            ),
        )
    if len(set(new_password)) == 1:
        raise BusinessError(
            ErrorCode.PASSWORD_POLICY_VIOLATION,
            'Пароль не должен состоять из одинаковых символов.',
        )
    if _is_monotonic_sequence(new_password):
        raise BusinessError(
            ErrorCode.PASSWORD_POLICY_VIOLATION,
            'Пароль не должен быть последовательностью символов.',
        )
    if new_password.casefold() in user.email.casefold():
        raise BusinessError(
            ErrorCode.PASSWORD_POLICY_VIOLATION,
            'Пароль не должен быть частью адреса электронной почты.',
        )
    if new_password.casefold() in WEAK_PASSWORDS:
        raise BusinessError(
            ErrorCode.PASSWORD_POLICY_VIOLATION, 'Слишком простой пароль.'
        )
    if new_password == current_password:
        raise BusinessError(
            ErrorCode.PASSWORD_POLICY_VIOLATION,
            'Новый пароль не должен совпадать с текущим.',
        )


async def change_password(
    session: AsyncSession, user: User, current_password: str, new_password: str
) -> User:
    """Меняет пароль по запросу пользователя.

    При отказе возбуждает BusinessError: INVALID_CREDENTIALS,
    ACCOUNT_NOT_ACTIVATED или PASSWORD_POLICY_VIOLATION.
    После успеха token_version увеличен, и все выпущенные ранее
    токены становятся недействительными.
    """
    await _require_valid_password(current_password, user.password_hash)
    validate_password_policy(new_password, user, current_password)
    user.token_version += 1
    user.password_hash = await hash_password(new_password)
    await session.commit()
    return user


async def force_logout(session: AsyncSession, user_id: uuid.UUID) -> None:
    """Увеличивает `token_version` пользователя.

    Отказ:
        - `NOT_FOUND` — пользователя с указанным id нет.
    """
    new_token_version = await increment_token_version(session, user_id)
    if new_token_version is None:
        raise BusinessError(ErrorCode.NOT_FOUND)
    await session.commit()
