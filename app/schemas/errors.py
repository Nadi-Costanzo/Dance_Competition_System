from pydantic import BaseModel, Field

from app.error_codes import ErrorCode, WarningCode


class ErrorResponse(BaseModel):
    """Единая структура тела ответа при ошибке прикладного кода."""

    code: ErrorCode = Field(description='Код ошибки (закрытый список)')
    detail: str = Field(description='Пояснение для пользователя')


class WarningItem(BaseModel):
    """Предупреждение в теле успешного ответа."""

    code: WarningCode = Field(
        description='Код предупреждения (закрытый список)'
    )
    detail: str = Field(description='Пояснение для пользователя')
