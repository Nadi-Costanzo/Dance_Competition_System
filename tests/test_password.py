import pytest

from app.auth.password import hash_password, verify_password


@pytest.mark.asyncio
async def test_hash_password_uses_random_salt() -> None:
    """Проверяет применение случайной соли для хеширования пароля."""
    password = 'secret'
    first_hash = await hash_password(password)
    second_hash = await hash_password(password)
    assert first_hash != second_hash


@pytest.mark.asyncio
async def test_verify_password_matches_only_correct_password() -> None:
    """Проверяет корректное поведение при правильном и неправильном пароле."""
    password = 'secret'
    wrong_password = 'wrong'
    test_hash = await hash_password(password)
    assert await verify_password(password, test_hash) is True
    assert await verify_password(wrong_password, test_hash) is False


@pytest.mark.asyncio
async def test_verify_passwords_longer_than_72_bytes() -> None:
    """Проверяет, что пароль длиннее 72 байт обрабатывается корректно."""
    long_password = 'пароль_из_сорока_символов_кириллицы_абвг'
    assert len(long_password.encode()) > 72, (
        'Пароль короче 72 байт: тест перестал различать Argon2id и bcrypt'
    )
    test_hash = await hash_password(long_password)
    other_password = long_password[:-1] + 'д'
    assert await verify_password(other_password, test_hash) is False
