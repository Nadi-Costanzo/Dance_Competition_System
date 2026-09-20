from typing import ClassVar

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Integer,
    String,
    false,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.constants import (
    EMAIL_MAX_LENGTH,
    FIO_MAX_LENGTH,
    JUDGE_CATEGORY_MAX_LENGTH,
    PASSWORD_HASH_MAX_LENGTH,
    ROLE_MAX_LENGTH,
    SYNC_ORIGIN_MAX_LENGTH,
    JudgeCategory,
    SyncOrigin,
    UserRole,
)
from app.models.base import ActivatableBase, sql_values_list


class User(ActivatableBase):
    """Пользователь системы.

    Учётная запись со ссылкой на роль и судейскую квалификацию.
    - `password_hash` пуст у пользователей, импортированных из облака, —
    пароль назначается отдельной процедурой активации.

    - `token_version` — механизм массового отзыва всех сессий пользователя.
    (forced logout всех access JWT). Refresh-токены, ротация refresh-токенов и
    таблица revoked_tokens добавляются только в Этапе 2.

    - `sync_origin` — пометка источника пользователя. (`local` — создан
    локально; `cloud` — импортирован из облака, пароль не задан.)
    """

    __tablename__ = 'users'
    __table_args__ = (
        CheckConstraint(
            f'role IN ({sql_values_list(UserRole)})', name='valid_role'
        ),
        CheckConstraint(
            f'judge_category IN ({sql_values_list(JudgeCategory)})',
            name='valid_judge_category',
        ),
        CheckConstraint(
            f'sync_origin IN ({sql_values_list(SyncOrigin)})',
            name='valid_sync_origin',
        ),
    )
    __repr_field__: ClassVar[str] = 'email'

    email: Mapped[str] = mapped_column(
        String(EMAIL_MAX_LENGTH),
        unique=True,
        nullable=False,
    )

    password_hash: Mapped[str | None] = mapped_column(
        String(PASSWORD_HASH_MAX_LENGTH),
    )

    surname: Mapped[str] = mapped_column(
        String(FIO_MAX_LENGTH),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(FIO_MAX_LENGTH),
        nullable=False,
        index=True,
    )

    patronymic: Mapped[str | None] = mapped_column(
        String(FIO_MAX_LENGTH),
        nullable=True,
    )
    role: Mapped[str] = mapped_column(
        String(ROLE_MAX_LENGTH),
        nullable=False,
        default=UserRole.USER,
        server_default=UserRole.USER,
    )
    is_certified_judge: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
    judge_category: Mapped[str | None] = mapped_column(
        String(JUDGE_CATEGORY_MAX_LENGTH),
    )

    token_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text('0'),
    )
    sync_origin: Mapped[str] = mapped_column(
        String(SYNC_ORIGIN_MAX_LENGTH),
        nullable=False,
        default=SyncOrigin.LOCAL,
        server_default=SyncOrigin.LOCAL,
    )
