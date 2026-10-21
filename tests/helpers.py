"""Вспомогательные функции тестов."""

import httpx

from app.error_codes import ErrorCode
from app.exceptions import ERROR_HTTP_STATUS, ERROR_MESSAGES
from tests.constants import TEST_PASSWORD


def assert_business_error(
    response: httpx.Response,
    code: ErrorCode,
    detail: str | None = None,
) -> None:
    """Проверяет ответ-отказ: статус, код и текст.

    Аргументы:
        - `response`: ответ клиента.
        - `code`: ожидаемый код отказа.
        - `detail`: ожидаемый текст; `None` — текст из ERROR_MESSAGES.
    """
    assert response.status_code == ERROR_HTTP_STATUS[code]
    data = response.json()
    assert data['code'] == code
    assert data['detail'] == (
        ERROR_MESSAGES[code] if detail is None else detail
    )


def login_body(email: str, password: str = TEST_PASSWORD) -> dict[str, str]:
    """Тело запроса `POST /auth/login`."""
    return {'email': email, 'password': password}
