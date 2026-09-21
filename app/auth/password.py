from fastapi.concurrency import run_in_threadpool
from pwdlib import PasswordHash

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
