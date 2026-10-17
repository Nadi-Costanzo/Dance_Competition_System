import uuid
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from app.auth.jwt import decode_token
from app.constants import TOKEN_FORMAT
from app.database import SessionDep
from app.error_codes import ErrorCode
from app.exceptions import BusinessError, TokenValidationError
from app.logging_config import get_logger
from app.models.user import User

logger = get_logger(__name__)

bearer_scheme = HTTPBearer(
    bearerFormat=TOKEN_FORMAT,
    auto_error=False,
)


CredentialsDep = Annotated[
    HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
]
"""Токен из заголовка `Authorization: Bearer`; None, если не передан."""


async def require_user(
    credentials: CredentialsDep,
    session: SessionDep,
) -> User:
    """Возвращает текущего аутентифицированного пользователя.

    Отказ:
    `INVALID_TOKEN` — заголовок не передан, токен не принят
        или пользователь из `sub` не найден;
    `TOKEN_VERSION_EXPIRED` — токен выпущен для старой версии пользователя;
    `ACCOUNT_DISABLED` — учётная запись отключена.
    """
    if credentials is None:
        raise BusinessError(ErrorCode.INVALID_TOKEN)
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except TokenValidationError as error:
        logger.warning('Токен не принят: %s', type(error.__cause__).__name__)
        raise BusinessError(ErrorCode.INVALID_TOKEN) from error
    # Чтобы пользователь получил ошибку 401 вместо 500, в decode_token
    # проверяется наличие полей. Здесь проверяем соответствие ожидаемым типам:
    try:
        user_id = uuid.UUID(payload['sub'])
        token_version = int(payload['token_version'])
    except (AttributeError, TypeError, ValueError) as error:
        logger.warning('Нарушена структура токена: %s', error)
        raise BusinessError(ErrorCode.INVALID_TOKEN) from error

    user: User | None = (
        await session.scalars(select(User).where(User.id == user_id))
    ).first()
    if user is None:
        logger.warning('Пользователь с id %s не найден.', user_id)
        raise BusinessError(ErrorCode.INVALID_TOKEN)

    if token_version != user.token_version:
        logger.info(
            'Версия токена %s не совпадает с версией пользователя %s',
            token_version,
            user.email,
        )
        raise BusinessError(ErrorCode.TOKEN_VERSION_EXPIRED)

    if not user.is_active:
        logger.info('Пользователь %s деактивирован.', user.email)
        raise BusinessError(ErrorCode.ACCOUNT_DISABLED)
    return user
