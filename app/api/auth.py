from fastapi import APIRouter

from app.api.responses import AUTH_LOGIN_RESPONSES, CHANGE_PASSWORD_RESPONSES
from app.auth.dependencies import CurrentUserDep
from app.auth.jwt import create_access_token
from app.constants import TOKEN_TYPE
from app.database import SessionDep
from app.logging_config import get_logger
from app.schemas.auth import (
    AccessTokenResponse,
    ChangePasswordRequestData,
    LoginRequestData,
)
from app.services.auth import authenticate, change_password

router = APIRouter()


logger = get_logger(__name__)


@router.post(
    '/login',
    response_model=AccessTokenResponse,
    responses=AUTH_LOGIN_RESPONSES,
)
async def login(
    user_data: LoginRequestData,
    session: SessionDep,
) -> AccessTokenResponse:
    """Аутентификация пользователя и получение токена доступа.

    - Возвращает токен доступа при успешной аутентификации.

    - Возвращает статус 401 при неверных учетных данных.

    - Возвращает статус 403 при отключённой учётной записи.
    """
    user = await authenticate(
        session,
        user_data.email,
        user_data.password.get_secret_value(),
    )
    access_token = create_access_token(user.id, user.token_version)
    logger.info('Пользователь успешно вошёл в систему: %s', user.email)
    return AccessTokenResponse(
        access_token=access_token, token_type=TOKEN_TYPE
    )


@router.post(
    '/change-password',
    response_model=AccessTokenResponse,
    responses=CHANGE_PASSWORD_RESPONSES,
)
async def change_own_password(
    user: CurrentUserDep,
    data: ChangePasswordRequestData,
    session: SessionDep,
) -> AccessTokenResponse:
    """Смена пароля и увеличение token_version.

    - Возвращает новый токен доступа при успешной смене пароля.

    - Возвращает статус 401 — токен не принят или текущий пароль не совпадает.

    - Возвращает статус 403 — учётная запись отключена.

    - Возвращает статус 422 — новый пароль не прошёл политику.
    """
    updated_user = await change_password(
        session=session,
        user=user,
        current_password=data.current_password.get_secret_value(),
        new_password=data.new_password.get_secret_value(),
    )
    access_token = create_access_token(
        updated_user.id, updated_user.token_version
    )
    logger.info('Пароль пользователя %s успешно изменён', user.email)
    return AccessTokenResponse(
        access_token=access_token, token_type=TOKEN_TYPE
    )
