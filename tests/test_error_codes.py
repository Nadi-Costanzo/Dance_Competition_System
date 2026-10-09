from collections.abc import Callable

from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.error_codes import ErrorCode
from app.exceptions import (
    ERROR_HTTP_STATUS,
    INTEGRITY_ERROR_CODES,
    BusinessError,
)
from tests.constants import TEST_ERROR_ROUTE


def test_every_error_code_has_http_status() -> None:
    """Для каждого кода определён HTTP-статус."""
    missing = set(ErrorCode) - set(ERROR_HTTP_STATUS)
    assert not missing, f'Отсутствует статус для: {missing}'


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
    expected_code, expected_detail = INTEGRITY_ERROR_CODES['users.email']
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
