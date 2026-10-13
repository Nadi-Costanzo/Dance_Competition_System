from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    SecretStr,
    field_validator,
)

from app.constants import TOKEN_TYPE


class LoginRequestData(BaseModel):
    """Схема данных для аутентификации."""

    model_config = ConfigDict(extra='forbid')
    email: EmailStr
    password: SecretStr

    @field_validator('email', mode='after')
    @classmethod
    def normalize_email(cls, email: EmailStr) -> EmailStr:
        """Приводит email к нижнему регистру.

        .strip() реализуется типом EmailStr
        """
        return email.lower()


class AccessTokenResponse(BaseModel):
    """Ответ на успешный вход: access-токен и его тип."""

    access_token: str
    token_type: str = TOKEN_TYPE
