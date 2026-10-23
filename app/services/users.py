from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.password import generate_temporary_password, hash_password
from app.constants import FIRST_ADMIN_EMAIL
from app.crud.user import add_first_admin, has_users
from app.logging_config import get_logger

logger = get_logger(__name__)


def _save_temporary_password(password: str, password_file: Path) -> None:
    """Пишет пароль в файл до фиксации транзакции.

    Порядок важен: если запись не удалась, администратор не фиксируется
    и следующий запуск создаст его заново.
    """
    password_file.write_text(password, encoding='utf-8')


def _announce_first_admin(password: str, password_file: Path) -> None:
    """Сообщает пароль в консоль и записывает событие в журнал.

    Пароль идёт мимо журнала: тот пишет и в logs/app.log,
    а пароль не должен сохраняться в открытом виде.
    """
    print(
        f'Временный пароль администратора {FIRST_ADMIN_EMAIL}: {password}\n'
        f'Пароль сохранён в файл {password_file} и показан один раз.'
    )
    logger.info(
        'Создан первый администратор: адрес %s, пароль в файле %s.',
        FIRST_ADMIN_EMAIL,
        password_file,
    )


async def ensure_first_admin(
    session: AsyncSession, password_file: Path
) -> str | None:
    """Создаёт первого администратора, если база пуста.

    Возвращает временный пароль или None, если администратор уже есть.
    """
    if await has_users(session):
        return None
    password = generate_temporary_password()
    await add_first_admin(session, await hash_password(password))

    _save_temporary_password(password, password_file)
    await session.commit()
    _announce_first_admin(password, password_file)
    return password
