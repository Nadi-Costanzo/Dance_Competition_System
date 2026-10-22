import uuid
from collections.abc import Awaitable, Callable

import httpx
import pytest
from fastapi import status

from app.constants import API_PREFIX
from app.error_codes import ErrorCode
from app.exceptions import ERROR_HTTP_STATUS
from app.main import app
from app.models.user import User
from tests.constants import TEST_PASSWORD, USER_EMAIL
from tests.helpers import assert_business_error, login_body

OTHER_PASSWORD = 'футбол1234'


@pytest.mark.asyncio
async def test_force_logout_returns_204_and_invalidates_token(
    async_client: httpx.AsyncClient,
    user: User,
    user_header: dict[str, str],
    admin_header: dict[str, str],
) -> None:
    """Инкремент token_version пользователя от имени администратора.

    Ответ: 204, старый токен дает 401 TOKEN_VERSION_EXPIRED.
    """
    force_logout_response = await async_client.post(
        f'{API_PREFIX}/users/{user.id}/force-logout',
        headers=admin_header,
    )
    change_password_response = await async_client.post(
        f'{API_PREFIX}/auth/change-password',
        json={
            'current_password': TEST_PASSWORD,
            'new_password': OTHER_PASSWORD,
        },
        headers=user_header,
    )
    assert force_logout_response.status_code == status.HTTP_204_NO_CONTENT
    assert not force_logout_response.content
    assert_business_error(
        change_password_response,
        ErrorCode.TOKEN_VERSION_EXPIRED,
    )


@pytest.mark.asyncio
async def test_user_can_login_with_same_password_after_force_logout(
    async_client: httpx.AsyncClient,
    user: User,
    admin_header: dict[str, str],
) -> None:
    """Пользователь успешно логинится после force-logout старым паролем."""
    await async_client.post(
        f'{API_PREFIX}/users/{user.id}/force-logout',
        headers=admin_header,
    )
    response = await async_client.post(
        f'{API_PREFIX}/auth/login', json=login_body(USER_EMAIL)
    )
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_force_logout_denies_regular_user(
    async_client: httpx.AsyncClient,
    user: User,
    user_header: dict[str, str],
) -> None:
    """Инкремент token_version пользователя от имени простого пользователя.

    Отказ:
    - 403 ACCESS_DENIED.
    """
    response = await async_client.post(
        f'{API_PREFIX}/users/{user.id}/force-logout',
        headers=user_header,
    )

    assert_business_error(
        response, ErrorCode.ACCESS_DENIED, 'Требуются права администратора'
    )


@pytest.mark.asyncio
async def test_force_logout_unknown_user_returns_not_found(
    async_client: httpx.AsyncClient,
    admin_header: dict[str, str],
) -> None:
    """Инкремент token_version несуществующего пользователя.

    Отказ:
    - 404 NOT_FOUND.
    """
    some_user_id = uuid.uuid4()
    response = await async_client.post(
        f'{API_PREFIX}/users/{some_user_id}/force-logout',
        headers=admin_header,
    )
    assert_business_error(response, ErrorCode.NOT_FOUND)


@pytest.mark.asyncio
async def test_admin_can_force_logout_self(
    async_client: httpx.AsyncClient,
    admin: User,
    admin_header: dict[str, str],
) -> None:
    """Инкремент token_version администратора от себя.

    Ответ: 204, старый токен дает 401 TOKEN_VERSION_EXPIRED.
    """
    force_logout_response = await async_client.post(
        f'{API_PREFIX}/users/{admin.id}/force-logout',
        headers=admin_header,
    )
    change_password_response = await async_client.post(
        f'{API_PREFIX}/auth/change-password',
        json={
            'current_password': TEST_PASSWORD,
            'new_password': OTHER_PASSWORD,
        },
        headers=admin_header,
    )
    assert force_logout_response.status_code == status.HTTP_204_NO_CONTENT
    assert not force_logout_response.content
    assert_business_error(
        change_password_response,
        ErrorCode.TOKEN_VERSION_EXPIRED,
    )


@pytest.mark.asyncio
async def test_force_logout_deactivated_user(
    async_client: httpx.AsyncClient,
    create_user: Callable[..., Awaitable[User]],
    admin_header: dict[str, str],
) -> None:
    """Инкремент token_version деактивированного пользователя.

    Ответ: 204.
    """
    deactivated_user = await create_user(is_active=False)
    force_logout_response = await async_client.post(
        f'{API_PREFIX}/users/{deactivated_user.id}/force-logout',
        headers=admin_header,
    )
    assert force_logout_response.status_code == status.HTTP_204_NO_CONTENT
    assert not force_logout_response.content


@pytest.mark.asyncio
async def test_force_logout_route_documents_error_responses() -> None:
    """Спецификация закрытого маршрута документирует отказы зависимости."""
    operation = app.openapi()['paths'][
        f'{API_PREFIX}/users/{{user_id}}/force-logout'
    ]['post']
    responses = operation['responses']
    no_content_key = str(status.HTTP_204_NO_CONTENT)
    assert no_content_key in responses
    assert 'content' not in responses[no_content_key]

    for code in (
        ErrorCode.ACCESS_DENIED,
        ErrorCode.NOT_FOUND,
        ErrorCode.TOKEN_VERSION_EXPIRED,
    ):
        status_key = str(ERROR_HTTP_STATUS[code])
        assert status_key in responses, (
            f'Статус {status_key} не найден в спецификации.'
        )
        schema = responses[status_key]['content']['application/json']
        assert schema['schema']['$ref'].endswith('ErrorResponse'), (
            f'Статус {status_key} не ссылается на ErrorResponse.'
        )
