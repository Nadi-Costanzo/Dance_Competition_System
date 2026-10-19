import pytest

from app.error_codes import ErrorCode
from app.exceptions import BusinessError
from app.models.user import User
from app.services.auth import validate_password_policy

REJECTED_PASSWORDS = [
    pytest.param('Short12', 'должен содержать от', id='too_short'),
    pytest.param(('ab' * 64 + 'c'), 'должен содержать от', id='too_long'),
    pytest.param('aaaaaaaa', 'одинаковых символов', id='repeated_char'),
    pytest.param('23456789', 'последовательностью', id='sequence_up'),
    pytest.param('87654321', 'последовательностью', id='sequence_down'),
    pytest.param('a.smirnova', 'почты', id='email_local_part'),
    pytest.param('a.smirnova@dcs.local', 'почты', id='email_full_address'),
    pytest.param('password', 'простой', id='weak_password_from_list'),
    pytest.param('PASSWORD', 'простой', id='weak_password_after_casefold'),
    pytest.param('Турнир-2026', 'совпадать', id='same_as_current_password'),
]

ACCEPTED_PASSWORDS = [
    pytest.param('Минимум8', id='at_min_length'),
    pytest.param(('фи' * 64), id='at_max_length'),
    pytest.param('базарбазар', id='repeated_word_allowed'),
    pytest.param('футбол1234', id='digits_in_phrase'),
    pytest.param('Турнир-2026-весна', id='extends_current_password'),
]

USER = User(email='a.smirnova@dcs.local', surname='Смирнова', name='Анна')
CURRENT_PASSWORD = 'Турнир-2026'


@pytest.mark.parametrize(
    ('new_password', 'expected_detail'), REJECTED_PASSWORDS
)
def test_policy_violation_names_the_rule(
    new_password: str, expected_detail: str
) -> None:
    """Отклонённый пароль даёт отказ с указанием нарушенного правила."""
    with pytest.raises(BusinessError, match=expected_detail) as error:
        validate_password_policy(new_password, USER, CURRENT_PASSWORD)
    assert error.value.code is ErrorCode.PASSWORD_POLICY_VIOLATION


@pytest.mark.parametrize('new_password', ACCEPTED_PASSWORDS)
def test_policy_accepts_valid_password(new_password: str) -> None:
    """Пароль, удовлетворяющий политике, проходит без отказа."""
    validate_password_policy(new_password, USER, CURRENT_PASSWORD)
