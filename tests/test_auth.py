from collections.abc import Awaitable, Callable

import httpx
import pytest
from fastapi import status

from app.auth.jwt import decode_token
from app.constants import API_PREFIX, TOKEN_TYPE
from app.error_codes import ErrorCode
from app.models.user import User
from tests.constants import TEST_PASSWORD, USER_EMAIL
from tests.helpers import assert_business_error


@pytest.mark.asyncio
async def test_login_correct_credentials_returns_token(
    async_client: httpx.AsyncClient,
    create_user: Callable[..., Awaitable[User]],
) -> None:
    """Верные учётные данные: ответ 200 и разбираемый токен."""
    user = await create_user()

    response = await async_client.post(
        f'{API_PREFIX}/auth/login',
        json={'email': USER_EMAIL, 'password': TEST_PASSWORD},
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
    """Неизвестный email: -> 401, INVALID_CREDENTIALS.

    Заголовок WWW-Authenticate: Bearer.
    """
    response = await async_client.post(
        f'{API_PREFIX}/auth/login',
        json={'email': USER_EMAIL, 'password': TEST_PASSWORD},
    )
    assert_business_error(response, ErrorCode.INVALID_CREDENTIALS)
    assert response.headers['www-authenticate'] == 'Bearer'


@pytest.mark.asyncio
async def test_login_wrong_password_returns_invalid_credentials(
    async_client: httpx.AsyncClient,
    create_user: Callable[..., Awaitable[User]],
) -> None:
    """Неверный пароль: -> 401, INVALID_CREDENTIALS.

    Заголовок WWW-Authenticate: Bearer.
    """
    await create_user(password='another_password')

    response = await async_client.post(
        f'{API_PREFIX}/auth/login',
        json={'email': USER_EMAIL, 'password': TEST_PASSWORD},
    )
    assert_business_error(response, ErrorCode.INVALID_CREDENTIALS)
    assert response.headers['www-authenticate'] == 'Bearer'


@pytest.mark.asyncio
async def test_login_disabled_user_returns_account_disabled(
    async_client: httpx.AsyncClient,
    create_user: Callable[..., Awaitable[User]],
) -> None:
    """Отключённый пользователь, верный пароль: -> 403 ACCOUNT_DISABLED.

    Заголовка WWW-Authenticate нет: повторное предъявление
    учётных данных не поможет.
    """
    await create_user(is_active=False)

    response = await async_client.post(
        f'{API_PREFIX}/auth/login',
        json={'email': USER_EMAIL, 'password': TEST_PASSWORD},
    )
    assert_business_error(response, ErrorCode.ACCOUNT_DISABLED)
    assert response.headers.get('www-authenticate') is None


@pytest.mark.asyncio
async def test_login_disabled_user_wrong_password(
    async_client: httpx.AsyncClient,
    create_user: Callable[..., Awaitable[User]],
) -> None:
    """Отключённый пользователь, неверный пароль: -> 401 INVALID_CREDENTIALS.

    Сведения о деактивации не сообщаются тому, кто не подтвердил
    владение записью: проверка is_active идёт после пароля.
    """
    await create_user(password='another_password', is_active=False)

    response = await async_client.post(
        f'{API_PREFIX}/auth/login',
        json={'email': USER_EMAIL, 'password': TEST_PASSWORD},
    )
    assert_business_error(response, ErrorCode.INVALID_CREDENTIALS)
    assert response.headers['www-authenticate'] == 'Bearer'


@pytest.mark.asyncio
async def test_login_user_without_password_returns_account_not_activated(
    async_client: httpx.AsyncClient,
    create_user: Callable[..., Awaitable[User]],
) -> None:
    """Запись без хеша пароля: -> 401, ACCOUNT_NOT_ACTIVATED.

    Сравнение паролей не выполняется: password_hash равен None.
    """
    await create_user(password=None)

    response = await async_client.post(
        f'{API_PREFIX}/auth/login',
        json={'email': USER_EMAIL, 'password': TEST_PASSWORD},
    )
    assert_business_error(response, ErrorCode.ACCOUNT_NOT_ACTIVATED)
    assert response.headers['www-authenticate'] == 'Bearer'


@pytest.mark.asyncio
async def test_invalid_credentials_detail_is_same_for_both_causes(
    async_client: httpx.AsyncClient,
    create_user: Callable[..., Awaitable[User]],
) -> None:
    """Нет записи и неверный пароль: одинаковый ответ.

    Разные тексты позволили бы перебором установить, какие адреса
    зарегистрированы.
    """
    request_body = {'email': USER_EMAIL, 'password': TEST_PASSWORD}

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


@pytest.mark.asyncio
async def test_change_password_wrong_current_password(
    async_client: httpx.AsyncClient,
    user_header: dict[str, str],
) -> None:
    """Введён неверный текущий пароль: -> 401 INVALID_CREDENTIALS."""
    password_request_data = {
        'current_password': 'Wrong_pass',
        'new_password': 'футбол1234',
    }
    response = await async_client.post(
        f'{API_PREFIX}/auth/change-password',
        json=password_request_data,
        headers=user_header,
    )
    assert_business_error(response, ErrorCode.INVALID_CREDENTIALS)


@pytest.mark.asyncio
async def test_change_password_same_as_current(
    async_client: httpx.AsyncClient,
    user_header: dict[str, str],
) -> None:
    """Новый пароль совпадает с текущим: -> 422 PASSWORD_POLICY_VIOLATION."""
    password_request_data = {
        'current_password': TEST_PASSWORD,
        'new_password': TEST_PASSWORD,
    }
    response = await async_client.post(
        f'{API_PREFIX}/auth/change-password',
        json=password_request_data,
        headers=user_header,
    )
    assert_business_error(
        response,
        ErrorCode.PASSWORD_POLICY_VIOLATION,
        'Новый пароль не должен совпадать с текущим.',
    )


@pytest.mark.asyncio
async def test_change_password_rotates_token(
    async_client: httpx.AsyncClient,
    user_token: str,
    user_header: dict[str, str],
) -> None:
    """Смена пароля выдаёт новый токен и инвалидирует старый.

    - Ответ 200 содержит новый access_token.

    - Старый токен отклоняется с кодом TOKEN_VERSION_EXPIRED.

    - Новый токен даёт доступ к защищённому эндпоинту.
    """
    first_password_request_data = {
        'current_password': TEST_PASSWORD,
        'new_password': 'футбол1234',
    }
    first_response = await async_client.post(
        f'{API_PREFIX}/auth/change-password',
        json=first_password_request_data,
        headers=user_header,
    )
    assert first_response.status_code == status.HTTP_200_OK

    new_token = first_response.json()['access_token']
    second_password_request_data = {
        'current_password': 'футбол1234',
        'new_password': 'Турнир-2026',
    }
    response_with_old_token = await async_client.post(
        f'{API_PREFIX}/auth/change-password',
        json=second_password_request_data,
        headers={'Authorization': f'Bearer {user_token}'},
    )
    assert_business_error(
        response_with_old_token, ErrorCode.TOKEN_VERSION_EXPIRED
    )
    response_with_new_token = await async_client.post(
        f'{API_PREFIX}/auth/change-password',
        json=second_password_request_data,
        headers={'Authorization': f'Bearer {new_token}'},
    )
    assert response_with_new_token.status_code == status.HTTP_200_OK
