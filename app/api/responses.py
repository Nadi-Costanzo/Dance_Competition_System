from typing import Any

from fastapi import status

from app.schemas.errors import ErrorResponse
from app.schemas.health import (
    HEALTH_DEGRADED_EXAMPLE,
    HEALTH_OK_EXAMPLE,
    HealthResponse,
)

ResponsesDict = dict[int | str, dict[str, Any]]

AUTH_LOGIN_RESPONSES: ResponsesDict = {
    status.HTTP_401_UNAUTHORIZED: {
        'model': ErrorResponse,
        'description': (
            'Неверный адрес или пароль; учётная запись не активирована'
        ),
    },
    status.HTTP_403_FORBIDDEN: {
        'model': ErrorResponse,
        'description': 'Учётная запись отключена',
    },
}

PROTECTED_RESPONSES: ResponsesDict = {
    status.HTTP_401_UNAUTHORIZED: {
        'model': ErrorResponse,
        'description': (
            'Токен отсутствует, не принят'
            ' или выпущен для прежней версии пользователя'
        ),
    },
    status.HTTP_403_FORBIDDEN: {
        'model': ErrorResponse,
        'description': 'Учётная запись отключена',
    },
}

HEALTH_CHECK_RESPONSES: ResponsesDict = {
    status.HTTP_200_OK: {
        'model': HealthResponse,
        'description': 'БД подключена, приложение работает',
        'content': {'application/json': {'example': HEALTH_OK_EXAMPLE}},
    },
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        'model': HealthResponse,
        'description': 'Отсутствует подключение к БД, приложение работает',
        'content': {'application/json': {'example': HEALTH_DEGRADED_EXAMPLE}},
    },
}

CHANGE_PASSWORD_RESPONSES: ResponsesDict = {
    status.HTTP_401_UNAUTHORIZED: {
        'model': ErrorResponse,
        'description': (
            'Токен отсутствует, не принят или выпущен для прежней версии'
            ' пользователя; переданный текущий пароль не совпадает'
        ),
    },
    status.HTTP_403_FORBIDDEN: {
        'model': ErrorResponse,
        'description': 'Учётная запись отключена',
    },
    status.HTTP_422_UNPROCESSABLE_CONTENT: {
        'model': ErrorResponse,
        'description': (
            'Новый пароль не соответствует политике — ErrorResponse'
            ' с code PASSWORD_POLICY_VIOLATION. Тело запроса, не прошедшее'
            ' валидацию схемы, даёт HTTPValidationError'
        ),
    },
}
