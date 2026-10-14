from collections.abc import Awaitable, Callable

import httpx
import pytest
from fastapi import status

from app.auth.jwt import decode_token
from app.constants import API_PREFIX, TOKEN_TYPE
from app.error_codes import ErrorCode
from app.exceptions import ERROR_HTTP_STATUS, ERROR_MESSAGES
from app.models.user import User
from tests.constants import TEST_EMAIL, TEST_PASSWORD


@pytest.mark.asyncio
async def test_login_correct_credentials_returns_token(
    async_client: httpx.AsyncClient,
    create_user: Callable[..., Awaitable[User]],
) -> None:
    """Верные учётные данные: ответ 200 и разбираемый токен."""
    user = await create_user()

    response = await async_client.post(
        f'{API_PREFIX}/auth/login',
        json={'email': TEST_EMAIL, 'password': TEST_PASSWORD},
    )
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data['token_type'] == TOKEN_TYPE
    payload = decode_token(data['access_token'])
    assert payload['sub'] == str(user.id)
    assert payload['token_version'] == user.token_version


@pytest.mark.asyncio
async def test_login_unknown_email(
    async_client: httpx.AsyncClient,
) -> None:
    """Неизвестный email: ответ 401, INVALID_CREDENTIALS.

    Заголовок WWW-Authenticate: Bearer.
    """
    response = await async_client.post(
        f'{API_PREFIX}/auth/login',
        json={'email': TEST_EMAIL, 'password': TEST_PASSWORD},
    )
    data = response.json()

    assert (
        response.status_code
        == ERROR_HTTP_STATUS[ErrorCode.INVALID_CREDENTIALS]
    )
    assert response.headers['www-authenticate'] == 'Bearer'
    assert data['code'] == ErrorCode.INVALID_CREDENTIALS
    assert data['detail'] == ERROR_MESSAGES[ErrorCode.INVALID_CREDENTIALS]


@pytest.mark.asyncio
async def test_login_wrong_password_returns_invalid_credentials(
    async_client: httpx.AsyncClient,
    create_user: Callable[..., Awaitable[User]],
) -> None:
    """Неверный пароль: ответ 401, INVALID_CREDENTIALS.

    Заголовок WWW-Authenticate: Bearer.
    """
    await create_user(password='another_password')

    response = await async_client.post(
        f'{API_PREFIX}/auth/login',
        json={'email': TEST_EMAIL, 'password': TEST_PASSWORD},
    )
    data = response.json()

    assert (
        response.status_code
        == ERROR_HTTP_STATUS[ErrorCode.INVALID_CREDENTIALS]
    )
    assert response.headers['www-authenticate'] == 'Bearer'
    assert data['code'] == ErrorCode.INVALID_CREDENTIALS
    assert data['detail'] == ERROR_MESSAGES[ErrorCode.INVALID_CREDENTIALS]


@pytest.mark.asyncio
async def test_login_disabled_user_returns_account_disabled(
    async_client: httpx.AsyncClient,
    create_user: Callable[..., Awaitable[User]],
) -> None:
    """Отключённый пользователь, верный пароль: ответ 403.

    Заголовка WWW-Authenticate нет: повторное предъявление
    учётных данных не поможет.
    """
    await create_user(is_active=False)

    response = await async_client.post(
        f'{API_PREFIX}/auth/login',
        json={'email': TEST_EMAIL, 'password': TEST_PASSWORD},
    )
    data = response.json()

    assert (
        response.status_code == ERROR_HTTP_STATUS[ErrorCode.ACCOUNT_DISABLED]
    )
    assert response.headers.get('www-authenticate') is None
    assert data['code'] == ErrorCode.ACCOUNT_DISABLED
    assert data['detail'] == ERROR_MESSAGES[ErrorCode.ACCOUNT_DISABLED]


@pytest.mark.asyncio
async def test_login_disabled_user_wrong_password(
    async_client: httpx.AsyncClient,
    create_user: Callable[..., Awaitable[User]],
) -> None:
    """Отключённый пользователь, неверный пароль: ответ 401.

    Сведения о деактивации не сообщаются тому, кто не подтвердил
    владение записью: проверка is_active идёт после пароля.
    """
    await create_user(password='another_password', is_active=False)

    response = await async_client.post(
        f'{API_PREFIX}/auth/login',
        json={'email': TEST_EMAIL, 'password': TEST_PASSWORD},
    )
    data = response.json()

    assert (
        response.status_code
        == ERROR_HTTP_STATUS[ErrorCode.INVALID_CREDENTIALS]
    )
    assert response.headers['www-authenticate'] == 'Bearer'
    assert data['code'] == ErrorCode.INVALID_CREDENTIALS
    assert data['detail'] == ERROR_MESSAGES[ErrorCode.INVALID_CREDENTIALS]


@pytest.mark.asyncio
async def test_login_user_without_password_returns_account_not_activated(
    async_client: httpx.AsyncClient,
    create_user: Callable[..., Awaitable[User]],
) -> None:
    """Запись без хеша пароля: ответ 401, ACCOUNT_NOT_ACTIVATED.

    Сравнение паролей не выполняется: password_hash равен None.
    """
    await create_user(password=None)

    response = await async_client.post(
        f'{API_PREFIX}/auth/login',
        json={'email': TEST_EMAIL, 'password': TEST_PASSWORD},
    )
    data = response.json()

    assert (
        response.status_code
        == ERROR_HTTP_STATUS[ErrorCode.ACCOUNT_NOT_ACTIVATED]
    )
    assert response.headers['www-authenticate'] == 'Bearer'
    assert data['code'] == ErrorCode.ACCOUNT_NOT_ACTIVATED
    assert data['detail'] == ERROR_MESSAGES[ErrorCode.ACCOUNT_NOT_ACTIVATED]


@pytest.mark.asyncio
async def test_invalid_credentials_detail_is_same_for_both_causes(
    async_client: httpx.AsyncClient,
    create_user: Callable[..., Awaitable[User]],
) -> None:
    """Нет записи и неверный пароль: одинаковый ответ.

    Разные тексты позволили бы перебором установить, какие адреса
    зарегистрированы.
    """
    request_body = {'email': TEST_EMAIL, 'password': TEST_PASSWORD}

    without_user = await async_client.post(
        f'{API_PREFIX}/auth/login', json=request_body
    )
    await create_user(password='another_password')
    with_user = await async_client.post(
        f'{API_PREFIX}/auth/login', json=request_body
    )

    first, second = without_user.json(), with_user.json()
    assert first['code'] == second['code'] == ErrorCode.INVALID_CREDENTIALS
    assert first['detail'] == second['detail']
