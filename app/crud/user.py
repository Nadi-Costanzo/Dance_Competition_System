from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Возвращает пользователя с указанным адресом или None."""
    result = await session.scalars(select(User).where(User.email == email))
    return result.first()
