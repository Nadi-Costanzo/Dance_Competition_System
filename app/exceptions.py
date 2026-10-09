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
DEFAULT_ERROR_STATUS = 409
"""HTTP-статус для кода, отсутствующего в ERROR_HTTP_STATUS."""

INTEGRITY_ERROR_CODES: dict[str, tuple[ErrorCode, str]] = {
    'users.email': (ErrorCode.EMAIL_ALREADY_EXISTS, 'Адрес уже занят'),
}


class BusinessError(Exception):
    """Нарушение бизнес-правила. Транслируется в ErrorResponse."""

    def __init__(self, code: ErrorCode, detail: str) -> None:
        """Сохраняет код и пояснение, определяет HTTP-статус по коду."""
        self.code = code
        self.detail = detail
        self.status_code = ERROR_HTTP_STATUS.get(code, DEFAULT_ERROR_STATUS)
        super().__init__(detail)
