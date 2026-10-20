import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import httpx
import jwt
import pytest
from fastapi import APIRouter, Depends, status

from app.api.responses import ADMIN_ONLY_RESPONSES, PROTECTED_RESPONSES
from app.auth.dependencies import AdminUser, require_user
from app.auth.jwt import create_access_token
from app.config import settings
from app.constants import (
    ACCESS_TOKEN_LIFETIME_HOURS,
    API_PREFIX,
    JWT_ALGORITHM,
    UserRole,
)
from app.error_codes import ErrorCode
from app.exceptions import ERROR_HTTP_STATUS, ERROR_MESSAGES
from app.main import app
from app.models.user import User

router = APIRouter(prefix=API_PREFIX)


@router.get(
    '/protected',
    responses=PROTECTED_RESPONSES,
)
async def protected(
    user: Annotated[User, Depends(require_user)],
) -> dict[str, str]:
    """Возвращает адрес текущего пользователя."""
    return {'email': user.email}


@router.get(
    '/only-admin',
    responses=ADMIN_ONLY_RESPONSES,
)
async def only_admin(
    admin: AdminUser,
) -> dict[str, str]:
    """Возвращает адрес администратора."""
    return {'email': admin.email}


app.include_router(router)


def auth_header(
    user: User, token_version: int | None = None
) -> dict[str, str]:
    """Собирает заголовок Authorization с токеном пользователя.

    Args:
        user: пользователь, от имени которого выпускается токен.
        token_version: версия для токена; None — текущая версия пользователя.
    """
    version = user.token_version if token_version is None else token_version
    return {'Authorization': f'Bearer {create_access_token(user.id, version)}'}


def make_token(payload: dict[str, Any], key: str | None = None) -> str:
    """Подписывает произвольный payload.

    Args:
        payload: состав токена — возможно, неполный.
        key: секретный ключ; None — ключ приложения.
    """
    secret = key or settings.jwt_secret_key.get_secret_value()
    return jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)


def valid_payload(user: User) -> dict[str, Any]:
    """Возвращает корректный payload; тест удаляет из него нужное поле."""
    lifetime = timedelta(hours=ACCESS_TOKEN_LIFETIME_HOURS)
    return {
        'sub': str(user.id),
        'token_version': user.token_version,
        'exp': datetime.now(UTC) + lifetime,
    }


@pytest.mark.asyncio
async def test_valid_token_returns_current_user(
    async_client: httpx.AsyncClient,
    create_user: Callable[..., Awaitable[User]],
) -> None:
    """Валидный токен: ответ 200 и адрес текущего пользователя."""
    user = await create_user()
    response = await async_client.get(
        f'{API_PREFIX}/protected', headers=auth_header(user)
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['email'] == user.email


@pytest.mark.asyncio
async def test_protected_route_requires_token(
    async_client: httpx.AsyncClient,
) -> None:
    """Без заголовка Authorization: ответ 401, INVALID_TOKEN."""
    response = await async_client.get(f'{API_PREFIX}/protected')
    data = response.json()
    assert response.status_code == ERROR_HTTP_STATUS[ErrorCode.INVALID_TOKEN]
    assert response.headers['www-authenticate'] == 'Bearer'
    assert data['code'] == ErrorCode.INVALID_TOKEN
    assert data['detail'] == ERROR_MESSAGES[ErrorCode.INVALID_TOKEN]


@pytest.mark.asyncio
async def test_non_bearer_scheme_is_rejected(
    async_client: httpx.AsyncClient,
) -> None:
    """Схема заголовка не Bearer: ответ 401, INVALID_TOKEN."""
    response = await async_client.get(
        f'{API_PREFIX}/protected', headers={'Authorization': 'Basic abc123'}
    )
    data = response.json()
    assert response.status_code == ERROR_HTTP_STATUS[ErrorCode.INVALID_TOKEN]
    assert response.headers['www-authenticate'] == 'Bearer'
    assert data['code'] == ErrorCode.INVALID_TOKEN
    assert data['detail'] == ERROR_MESSAGES[ErrorCode.INVALID_TOKEN]


@pytest.mark.asyncio
async def test_malformed_token_is_rejected(
    async_client: httpx.AsyncClient,
) -> None:
    """Значение токена не JWT: ответ 401, INVALID_TOKEN."""
    response = await async_client.get(
        f'{API_PREFIX}/protected',
        headers={'Authorization': 'Bearer not-a-jwt'},
    )
    data = response.json()
    assert response.status_code == ERROR_HTTP_STATUS[ErrorCode.INVALID_TOKEN]
    assert response.headers['www-authenticate'] == 'Bearer'
    assert data['code'] == ErrorCode.INVALID_TOKEN
    assert data['detail'] == ERROR_MESSAGES[ErrorCode.INVALID_TOKEN]


@pytest.mark.asyncio
async def test_token_signed_with_another_key_is_rejected(
    async_client: httpx.AsyncClient,
    create_user: Callable[..., Awaitable[User]],
) -> None:
    """Токен подписан другим ключом: ответ 401, INVALID_TOKEN."""
    user = await create_user()
    payload = valid_payload(user)
    token = make_token(
        payload, key='We_use_long_WRONG-secret-key!_WRONG-secret-key'
    )
    response = await async_client.get(
        f'{API_PREFIX}/protected', headers={'Authorization': f'Bearer {token}'}
    )
    data = response.json()
    assert response.status_code == ERROR_HTTP_STATUS[ErrorCode.INVALID_TOKEN]
    assert response.headers['www-authenticate'] == 'Bearer'
    assert data['code'] == ErrorCode.INVALID_TOKEN
    assert data['detail'] == ERROR_MESSAGES[ErrorCode.INVALID_TOKEN]


@pytest.mark.asyncio
async def test_expired_token_is_rejected(
    async_client: httpx.AsyncClient,
    create_user: Callable[..., Awaitable[User]],
) -> None:
    """Истёкший токен: ответ 401, INVALID_TOKEN."""
    user = await create_user()
    payload = valid_payload(user)
    payload['exp'] = datetime.now(UTC) - timedelta(hours=1)
    token = make_token(payload)
    response = await async_client.get(
        f'{API_PREFIX}/protected', headers={'Authorization': f'Bearer {token}'}
    )
    data = response.json()
    assert response.status_code == ERROR_HTTP_STATUS[ErrorCode.INVALID_TOKEN]
    assert response.headers['www-authenticate'] == 'Bearer'
    assert data['code'] == ErrorCode.INVALID_TOKEN
    assert data['detail'] == ERROR_MESSAGES[ErrorCode.INVALID_TOKEN]


@pytest.mark.asyncio
async def test_token_without_exp_is_rejected(
    async_client: httpx.AsyncClient,
    create_user: Callable[..., Awaitable[User]],
) -> None:
    """Токен без поля exp: ответ 401, INVALID_TOKEN."""
    user = await create_user()
    payload = valid_payload(user)
    del payload['exp']
    token = make_token(payload)
    response = await async_client.get(
        f'{API_PREFIX}/protected', headers={'Authorization': f'Bearer {token}'}
    )
    data = response.json()
    assert response.status_code == ERROR_HTTP_STATUS[ErrorCode.INVALID_TOKEN]
    assert response.headers['www-authenticate'] == 'Bearer'
    assert data['code'] == ErrorCode.INVALID_TOKEN
    assert data['detail'] == ERROR_MESSAGES[ErrorCode.INVALID_TOKEN]


@pytest.mark.asyncio
async def test_token_with_not_a_uuid_sub_is_rejected(
    async_client: httpx.AsyncClient,
    create_user: Callable[..., Awaitable[User]],
) -> None:
    """Токен с значением sub, не являющимся UUID: ответ 401, INVALID_TOKEN."""
    user = await create_user()
    payload = valid_payload(user)
    payload['sub'] = 'not-a-uuid'
    token = make_token(payload)
    response = await async_client.get(
        f'{API_PREFIX}/protected', headers={'Authorization': f'Bearer {token}'}
    )
    data = response.json()
    assert response.status_code == ERROR_HTTP_STATUS[ErrorCode.INVALID_TOKEN]
    assert response.headers['www-authenticate'] == 'Bearer'
    assert data['code'] == ErrorCode.INVALID_TOKEN
    assert data['detail'] == ERROR_MESSAGES[ErrorCode.INVALID_TOKEN]


@pytest.mark.asyncio
async def test_token_with_str_token_version_is_rejected(
    async_client: httpx.AsyncClient,
    create_user: Callable[..., Awaitable[User]],
) -> None:
    """Токен со строковой версией token_version: ответ 401, INVALID_TOKEN."""
    user = await create_user()
    payload = valid_payload(user)
    payload['token_version'] = 'ноль'
    token = make_token(payload)
    response = await async_client.get(
        f'{API_PREFIX}/protected', headers={'Authorization': f'Bearer {token}'}
    )
    data = response.json()
    assert response.status_code == ERROR_HTTP_STATUS[ErrorCode.INVALID_TOKEN]
    assert response.headers['www-authenticate'] == 'Bearer'
    assert data['code'] == ErrorCode.INVALID_TOKEN
    assert data['detail'] == ERROR_MESSAGES[ErrorCode.INVALID_TOKEN]


@pytest.mark.asyncio
async def test_token_without_token_version_is_rejected(
    async_client: httpx.AsyncClient,
    create_user: Callable[..., Awaitable[User]],
) -> None:
    """Токен без поля token_version: ответ 401, INVALID_TOKEN."""
    user = await create_user()
    payload = valid_payload(user)
    del payload['token_version']
    token = make_token(payload)
    response = await async_client.get(
        f'{API_PREFIX}/protected', headers={'Authorization': f'Bearer {token}'}
    )
    data = response.json()
    assert response.status_code == ERROR_HTTP_STATUS[ErrorCode.INVALID_TOKEN]
    assert response.headers['www-authenticate'] == 'Bearer'
    assert data['code'] == ErrorCode.INVALID_TOKEN
    assert data['detail'] == ERROR_MESSAGES[ErrorCode.INVALID_TOKEN]


@pytest.mark.asyncio
async def test_token_with_unknown_sub_is_rejected(
    async_client: httpx.AsyncClient,
    create_user: Callable[..., Awaitable[User]],
) -> None:
    """Токен с неизвестным sub: ответ 401, INVALID_TOKEN."""
    user = await create_user()
    payload = valid_payload(user)
    payload['sub'] = str(uuid.uuid4())
    token = make_token(payload)
    response = await async_client.get(
        f'{API_PREFIX}/protected', headers={'Authorization': f'Bearer {token}'}
    )
    data = response.json()
    assert response.status_code == ERROR_HTTP_STATUS[ErrorCode.INVALID_TOKEN]
    assert response.headers['www-authenticate'] == 'Bearer'
    assert data['code'] == ErrorCode.INVALID_TOKEN
    assert data['detail'] == ERROR_MESSAGES[ErrorCode.INVALID_TOKEN]


@pytest.mark.asyncio
async def test_stale_token_version_is_rejected(
    async_client: httpx.AsyncClient,
    create_user: Callable[..., Awaitable[User]],
) -> None:
    """Токен с устаревшей версией: ответ 401, TOKEN_VERSION_EXPIRED."""
    user = await create_user()
    response = await async_client.get(
        f'{API_PREFIX}/protected',
        headers=auth_header(user, user.token_version + 1),
    )
    data = response.json()
    assert (
        response.status_code
        == ERROR_HTTP_STATUS[ErrorCode.TOKEN_VERSION_EXPIRED]
    )
    assert response.headers['www-authenticate'] == 'Bearer'
    assert data['code'] == ErrorCode.TOKEN_VERSION_EXPIRED
    assert data['detail'] == ERROR_MESSAGES[ErrorCode.TOKEN_VERSION_EXPIRED]


@pytest.mark.asyncio
async def test_disabled_user_is_rejected(
    async_client: httpx.AsyncClient,
    create_user: Callable[..., Awaitable[User]],
) -> None:
    """Отключённый пользователь, верный токен: ответ 403, ACCOUNT_DISABLED."""
    user = await create_user(is_active=False)
    response = await async_client.get(
        f'{API_PREFIX}/protected', headers=auth_header(user)
    )
    data = response.json()
    assert (
        response.status_code == ERROR_HTTP_STATUS[ErrorCode.ACCOUNT_DISABLED]
    )
    assert 'www-authenticate' not in response.headers
    assert data['code'] == ErrorCode.ACCOUNT_DISABLED
    assert data['detail'] == ERROR_MESSAGES[ErrorCode.ACCOUNT_DISABLED]


@pytest.mark.asyncio
async def test_version_is_checked_before_is_active(
    async_client: httpx.AsyncClient,
    create_user: Callable[..., Awaitable[User]],
) -> None:
    """Проверка версии токена идёт раньше проверки is_active.

    Отключённый пользователь, токен с устаревшей версией: ответ 401,
    TOKEN_VERSION_EXPIRED, а не 403 ACCOUNT_DISABLED.
    """
    user = await create_user(is_active=False)
    response = await async_client.get(
        f'{API_PREFIX}/protected',
        headers=auth_header(user, user.token_version + 1),
    )
    data = response.json()
    assert (
        response.status_code
        == ERROR_HTTP_STATUS[ErrorCode.TOKEN_VERSION_EXPIRED]
    )
    assert response.headers['www-authenticate'] == 'Bearer'
    assert data['code'] == ErrorCode.TOKEN_VERSION_EXPIRED
    assert data['detail'] == ERROR_MESSAGES[ErrorCode.TOKEN_VERSION_EXPIRED]


def test_protected_route_documents_error_responses() -> None:
    """Спецификация защищённого маршрута документирует отказы зависимости."""
    operation = app.openapi()['paths'][f'{API_PREFIX}/protected']['get']
    responses = operation['responses']
    for code in (
        ErrorCode.INVALID_TOKEN,
        ErrorCode.TOKEN_VERSION_EXPIRED,
        ErrorCode.ACCOUNT_DISABLED,
    ):
        status_key = str(ERROR_HTTP_STATUS[code])
        assert status_key in responses, (
            f'Статус {status_key} не найден в спецификации.'
        )
        schema = responses[status_key]['content']['application/json']
        assert schema['schema']['$ref'].endswith('ErrorResponse'), (
            f'Статус {status_key} не ссылается на ErrorResponse.'
        )


@pytest.mark.asyncio
async def test_only_admin_allows_admin(
    async_client: httpx.AsyncClient,
    create_user: Callable[..., Awaitable[User]],
) -> None:
    """Администратор получает 200 и свой email."""
    user = await create_user(role=UserRole.ADMIN)
    response = await async_client.get(
        f'{API_PREFIX}/only-admin', headers=auth_header(user)
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['email'] == user.email


@pytest.mark.asyncio
async def test_only_admin_denies_regular_user(
    async_client: httpx.AsyncClient,
    create_user: Callable[..., Awaitable[User]],
) -> None:
    """User получает ответ 403 ACCESS_DENIED."""
    user = await create_user()
    response = await async_client.get(
        f'{API_PREFIX}/only-admin', headers=auth_header(user)
    )
    data = response.json()
    assert response.status_code == ERROR_HTTP_STATUS[ErrorCode.ACCESS_DENIED]
    assert data['code'] == ErrorCode.ACCESS_DENIED
    assert data['detail'] == 'Требуются права администратора'


@pytest.mark.asyncio
async def test_activity_is_checked_before_role(
    async_client: httpx.AsyncClient,
    create_user: Callable[..., Awaitable[User]],
) -> None:
    """Деактивированный администратор получает ответ 403 ACCOUNT_DISABLED."""
    user = await create_user(
        role=UserRole.ADMIN,
        is_active=False,
    )
    response = await async_client.get(
        f'{API_PREFIX}/only-admin', headers=auth_header(user)
    )
    data = response.json()
    assert (
        response.status_code == ERROR_HTTP_STATUS[ErrorCode.ACCOUNT_DISABLED]
    )
    assert data['code'] == ErrorCode.ACCOUNT_DISABLED
    assert data['detail'] == ERROR_MESSAGES[ErrorCode.ACCOUNT_DISABLED]


@pytest.mark.asyncio
async def test_only_admin_route_documents_error_responses() -> None:
    """Спецификация закрытого маршрута документирует отказы зависимости."""
    operation = app.openapi()['paths'][f'{API_PREFIX}/only-admin']['get']
    responses = operation['responses']
    for code in (
        ErrorCode.INVALID_TOKEN,
        ErrorCode.TOKEN_VERSION_EXPIRED,
        ErrorCode.ACCOUNT_DISABLED,
        ErrorCode.ACCESS_DENIED,
    ):
        status_key = str(ERROR_HTTP_STATUS[code])
        assert status_key in responses, (
            f'Статус {status_key} не найден в спецификации.'
        )
        schema = responses[status_key]['content']['application/json']
        assert schema['schema']['$ref'].endswith('ErrorResponse'), (
            f'Статус {status_key} не ссылается на ErrorResponse.'
        )
