from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.error_codes import ErrorCode
from app.exceptions import (
    ERROR_HTTP_STATUS,
    ERROR_MESSAGES,
    INTEGRITY_ERROR_CODES,
    BusinessError,
)
from tests.constants import TEST_ERROR_ROUTE


def test_every_error_code_has_http_status() -> None:
    """Для каждого кода определён HTTP-статус."""
    missing = set(ErrorCode) - set(ERROR_HTTP_STATUS)
    assert not missing, f'Отсутствует статус для: {missing}'


def test_every_error_code_has_default_message() -> None:
    """Для каждого кода определён текст по умолчанию."""
    missing = set(ErrorCode) - set(ERROR_MESSAGES)
    assert not missing, f'Отсутствует текст по умолчанию для: {missing}'


def test_business_error_response_has_detail_and_status(
    client_raising: Callable[..., TestClient],
) -> None:
    """Ответ при ошибке содержит поля detail и code, входящий в перечень."""
    client = client_raising(
        BusinessError(ErrorCode.NOT_FOUND, 'Ошибка для теста')
    )
    response = client.get(TEST_ERROR_ROUTE)
    data = response.json()
    assert response.status_code == ERROR_HTTP_STATUS[ErrorCode.NOT_FOUND]
    assert data.keys() == {'code', 'detail'}
    ErrorCode(data['code'])


def test_unknown_constraint_gives_500(
    client_raising: Callable[..., TestClient],
) -> None:
    """Непредусмотренное ограничение не маскируется под бизнес-ошибку."""
    client = client_raising(
        IntegrityError(
            'stmt', {}, Exception('UNIQUE constraint failed: other.col')
        ),
        raise_server_exceptions=False,
    )
    assert client.get(TEST_ERROR_ROUTE).status_code == 500


def test_known_constraint_translated_to_error_code(
    client_raising: Callable[..., TestClient],
) -> None:
    """Предусмотренное ограничение даёт код из INTEGRITY_ERROR_CODES."""
    expected_code = INTEGRITY_ERROR_CODES['users.email']
    expected_detail = ERROR_MESSAGES[expected_code]
    client = client_raising(
        IntegrityError(
            'stmt', {}, Exception('UNIQUE constraint failed: users.email')
        )
    )
    response = client.get(TEST_ERROR_ROUTE)
    data = response.json()

    assert response.status_code == ERROR_HTTP_STATUS[expected_code]
    assert data['code'] == expected_code
    assert data['detail'] == expected_detail


@pytest.mark.parametrize('code', list(ErrorCode))
def test_business_error_uses_default_message(code: ErrorCode) -> None:
    """Без detail берётся текст по умолчанию, он же попадает в str()."""
    error = BusinessError(code)
    assert error.detail == ERROR_MESSAGES[code]
    assert str(error) == error.detail
