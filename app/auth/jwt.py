import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.config import settings
from app.constants import ACCESS_TOKEN_LIFETIME_HOURS, JWT_ALGORITHM
from app.exceptions import TokenValidationError
from app.logging_config import get_logger

logger = get_logger(__name__)


def create_access_token(user_id: uuid.UUID, token_version: int) -> str:
    """Генерация JWT токена."""
    expire = datetime.now(UTC) + timedelta(hours=ACCESS_TOKEN_LIFETIME_HOURS)
    payload = {
        'sub': str(user_id),
        'token_version': token_version,
        'exp': expire,
    }
    encoded = jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=JWT_ALGORITHM,
    )
    logger.debug('Выдан токен пользователю %s', user_id)
    return encoded


def decode_token(token: str) -> dict[str, Any]:
    """Проверяет подпись и срок действия токена, возвращает payload."""
    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[JWT_ALGORITHM],
        )
    except jwt.InvalidTokenError as error:
        raise TokenValidationError('Токен недействителен') from error
