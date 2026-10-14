import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.auth.jwt import create_access_token, decode_token
from app.config import settings
from app.constants import ACCESS_TOKEN_LIFETIME_HOURS, JWT_ALGORITHM
from app.exceptions import TokenValidationError


def test_token_payload_composition() -> None:
    """Проверяет состав словаря payload."""
    user_id = uuid.uuid4()
    token = create_access_token(user_id=user_id, token_version=3)
    data = jwt.decode(token, options={'verify_signature': False})
    assert data.keys() == {'sub', 'token_version', 'exp'}
    assert data['sub'] == str(user_id)
    assert data['token_version'] == 3

    expected = datetime.now(UTC) + timedelta(hours=ACCESS_TOKEN_LIFETIME_HOURS)
    actual = datetime.fromtimestamp(data['exp'], UTC)
    assert abs((actual - expected).total_seconds()) < 5


def test_token_with_alg_none_is_rejected() -> None:
    """Токен с alg=none и без подписи не принимается."""
    user_id = uuid.uuid4()
    expire = datetime.now(UTC) + timedelta(hours=ACCESS_TOKEN_LIFETIME_HOURS)
    # Вручную собираем "злой" токен: alg=none, без подписи
    payload = {
        'sub': str(user_id),
        'token_version': 3,
        'exp': expire,
    }
    evil_token = jwt.encode(payload, key='', algorithm='none')

    with pytest.raises(TokenValidationError):
        decode_token(evil_token)


def test_expired_token_is_rejected() -> None:
    """Просроченный токен не принимается."""
    user_id = uuid.uuid4()
    # Вручную собираем "устаревший" токен
    expire = datetime.now(UTC) - timedelta(hours=1)
    payload = {
        'sub': str(user_id),
        'token_version': 3,
        'exp': expire,
    }
    old_token = jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=JWT_ALGORITHM,
    )
    with pytest.raises(TokenValidationError) as exc_info:
        decode_token(old_token)
    assert isinstance(exc_info.value.__cause__, jwt.ExpiredSignatureError)


def test_token_with_wrong_key_is_rejected() -> None:
    """Токен, подписанный чужим ключом, не принимается."""
    user_id = uuid.uuid4()
    # Вручную собираем "чужой" токен
    expire = datetime.now(UTC) + timedelta(hours=ACCESS_TOKEN_LIFETIME_HOURS)
    payload = {
        'sub': str(user_id),
        'token_version': 3,
        'exp': expire,
    }
    other_token = jwt.encode(
        payload,
        'We_use_long_WRONG-secret-key!_WRONG-secret-key',
        algorithm=JWT_ALGORITHM,
    )
    with pytest.raises(TokenValidationError) as exc_info:
        decode_token(other_token)
    assert isinstance(exc_info.value.__cause__, jwt.InvalidSignatureError)


def test_non_token_is_rejected() -> None:
    """Строка, не являющаяся токеном, не принимается."""
    with pytest.raises(TokenValidationError) as exc_info:
        decode_token('non_token')
    assert isinstance(exc_info.value.__cause__, jwt.DecodeError)


def test_valid_token_is_accepted() -> None:
    """Decode принимает правильный токен."""
    user_id = uuid.uuid4()
    token = create_access_token(user_id=user_id, token_version=3)
    data = decode_token(token)
    assert data['sub'] == str(user_id)
