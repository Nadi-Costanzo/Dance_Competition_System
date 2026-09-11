from typing import Literal

from pydantic import BaseModel, Field


class DbCheck(BaseModel):
    """Результат проверки одной зависимости."""

    status: Literal['ok', 'error']
    latency_ms: int | None = Field(
        default=None,
        description='Длительность текущего соединения (только при status=ok)',
    )
    reason: Literal['db_unavailable', 'db_locked', 'db_timeout'] | None = (
        Field(
            default=None,
            description='Диагностический код (только при status=error)',
        )
    )
    detail: str | None = Field(
        default=None,
        description='Человекочитаемое пояснение без пути к БД и стектрейса',
    )


class HealthChecks(BaseModel):
    """Объект checks: ключ на каждую зависимость."""

    db: DbCheck


class HealthResponse(BaseModel):
    """Единая схема ответа /health для 200 и 503."""

    status: Literal['ok', 'degraded']
    version: str
    uptime_sec: int
    checks: HealthChecks
