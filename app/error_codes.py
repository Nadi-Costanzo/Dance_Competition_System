from enum import StrEnum


class ErrorCode(StrEnum):
    """Коды бизнес-ошибок. Перечень закрытый."""

    ACCESS_DENIED = 'ACCESS_DENIED'
    ACCOUNT_DISABLED = 'ACCOUNT_DISABLED'
    ACCOUNT_NOT_ACTIVATED = 'ACCOUNT_NOT_ACTIVATED'
    EMAIL_ALREADY_EXISTS = 'EMAIL_ALREADY_EXISTS'
    INVALID_CREDENTIALS = 'INVALID_CREDENTIALS'
    INVALID_TOKEN = 'INVALID_TOKEN'
    NOT_FOUND = 'NOT_FOUND'
    TOKEN_VERSION_EXPIRED = 'TOKEN_VERSION_EXPIRED'


class WarningCode(StrEnum):
    """Коды предупреждений. Перечень закрытый."""

    JUDGE_NOT_CERTIFIED = 'JUDGE_NOT_CERTIFIED'
