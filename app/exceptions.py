from app.error_codes import ErrorCode

ERROR_HTTP_STATUS: dict[ErrorCode, int] = {
    ErrorCode.INVALID_CREDENTIALS: 401,
    ErrorCode.ACCOUNT_NOT_ACTIVATED: 401,
    ErrorCode.ACCOUNT_DISABLED: 403,
    ErrorCode.INVALID_TOKEN: 401,
    ErrorCode.ACCESS_DENIED: 403,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.EMAIL_ALREADY_EXISTS: 409,
    ErrorCode.TOKEN_VERSION_EXPIRED: 401,
}

ERROR_MESSAGES: dict[ErrorCode, str] = {
    ErrorCode.INVALID_CREDENTIALS: 'Неверный адрес или пароль.',
    ErrorCode.ACCOUNT_NOT_ACTIVATED: (
        'Учётная запись не активирована. Обратитесь к администратору.'
    ),
    ErrorCode.ACCOUNT_DISABLED: (
        'Учётная запись отключена. Обратитесь к администратору.'
    ),
    ErrorCode.INVALID_TOKEN: 'Недействительный токен.',
    ErrorCode.ACCESS_DENIED: 'Доступ запрещён.',
    ErrorCode.NOT_FOUND: 'Объект не найден.',
    ErrorCode.EMAIL_ALREADY_EXISTS: 'Адрес уже занят.',
    ErrorCode.TOKEN_VERSION_EXPIRED: 'Сессия устарела, войдите заново.',
}


INTEGRITY_ERROR_CODES: dict[str, ErrorCode] = {
    'users.email': ErrorCode.EMAIL_ALREADY_EXISTS,
}


class BusinessError(Exception):
    """Нарушение бизнес-правила. Транслируется в ErrorResponse."""

    def __init__(self, code: ErrorCode, detail: str | None = None) -> None:
        """Сохраняет код и пояснение, определяет HTTP-статус по коду."""
        self.code = code
        self.detail = detail or ERROR_MESSAGES[code]
        self.status_code = ERROR_HTTP_STATUS[code]
        super().__init__(self.detail)


class TokenValidationError(Exception):
    """Универсальное исключение для ошибок валидации токена."""
