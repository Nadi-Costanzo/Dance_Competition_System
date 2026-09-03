from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

from app.constants import NAMING_CONVENTION


class Base(DeclarativeBase):
    """Базовый класс ORM для БД, от которого наследуются все модели."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
