import secrets

from fastapi.concurrency import run_in_threadpool
from pwdlib import PasswordHash

from app.constants import TEMPORARY_PASSWORD_BYTES

_hasher = PasswordHash.recommended()


async def hash_password(password: str) -> str:
    """Возвращает хеш пароля (Argon2id)."""
    return await run_in_threadpool(_hasher.hash, password)


async def verify_password(password: str, password_hash: str) -> bool:
    """Проверяет соответствие пароля сохранённому хешу."""
    return await run_in_threadpool(
        _hasher.verify,
        password,
        password_hash,
    )


def generate_temporary_password() -> str:
    """Возвращает временный пароль: 16 hex-символов, 64 бита энтропии."""
    return secrets.token_hex(TEMPORARY_PASSWORD_BYTES)
