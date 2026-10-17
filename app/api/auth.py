from fastapi import APIRouter

from app.api.responses import AUTH_LOGIN_RESPONSES
from app.auth.jwt import create_access_token
from app.constants import TOKEN_TYPE
from app.database import SessionDep
from app.logging_config import get_logger
from app.schemas.auth import AccessTokenResponse, LoginRequestData
from app.services.auth import authenticate

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
