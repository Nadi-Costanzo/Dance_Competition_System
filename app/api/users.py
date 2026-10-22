import uuid

from fastapi import APIRouter, status

from app.api.responses import FORCE_LOGOUT_RESPONSES
from app.auth.dependencies import AdminUser
from app.database import SessionDep
from app.logging_config import get_logger
from app.services.auth import force_logout

router = APIRouter()

logger = get_logger(__name__)


@router.post(
    '/{user_id}/force-logout',
    status_code=status.HTTP_204_NO_CONTENT,
    responses=FORCE_LOGOUT_RESPONSES,
)
async def force_logout_user(
    user_id: uuid.UUID, session: SessionDep, admin: AdminUser
) -> None:
    """Завершает сессии пользователя: поднимает `token_version`.

    - Возвращает статус 204 — сессии пользователя завершены.

    - Возвращает статус 401 — токен не принят или устарел.

    - Возвращает статус 403 — нет прав или учётная запись отключена.

    - Возвращает статус 404 — пользователя с указанным id нет.
    """
    await force_logout(session, user_id)
    logger.info(
        'Администратор %s завершил сессии пользователя %s',
        admin.id,
        user_id,
    )
