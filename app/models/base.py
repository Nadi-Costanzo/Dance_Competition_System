import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import ClassVar

from sqlalchemy import Boolean, DateTime, MetaData, Uuid, true
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func

from app.constants import NAMING_CONVENTION


def sql_values_list(enum_class: type[StrEnum]) -> str:
    """Возвращает значения перечисления как список для SQL-оператора IN."""
    values = [f"'{item.value}'" for item in enum_class]
    return ', '.join(values)


class Base(DeclarativeBase):
    """Базовый класс ORM: метаданные, первичный ключ, время создания."""

    __repr_field__: ClassVar[str | None] = None
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        """Универсальное строковое представление для отладки."""
        if self.__repr_field__ is None:
            return f'<{self.__class__.__name__} id={self.id}>'
        value = getattr(self, self.__repr_field__)
        return (
            f'<{self.__class__.__name__} '
            f'id={self.id} {self.__repr_field__}={value!r}>'
        )


class MutableBase(Base):
    """Изменяемые сущности: добавляет время последнего изменения."""

    __abstract__ = True
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class ActivatableBase(MutableBase):
    """Сущности с признаком активности (мягкое удаление)."""

    __abstract__ = True
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        server_default=true(),
    )
