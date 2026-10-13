from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.password import verify_password
from app.crud.user import get_user_by_email
from app.error_codes import ErrorCode
from app.exceptions import BusinessError
from app.models.user import User


async def authenticate(
    session: AsyncSession, email: str, password: str
) -> User:
    """Проверяет email и пароль, возвращает пользователя.

    При отказе возбуждает BusinessError.
    """
    user = await get_user_by_email(session, email)
    if user is None:
        raise BusinessError(ErrorCode.INVALID_CREDENTIALS)
    if user.password_hash is None:
        raise BusinessError(ErrorCode.ACCOUNT_NOT_ACTIVATED)
    if not await verify_password(password, user.password_hash):
        raise BusinessError(ErrorCode.INVALID_CREDENTIALS)
    if not user.is_active:
        raise BusinessError(ErrorCode.ACCOUNT_DISABLED)
    return user
