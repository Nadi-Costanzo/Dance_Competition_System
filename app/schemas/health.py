from typing import Literal

from pydantic import BaseModel, Field

from app.constants import DB_DETAIL_UNAVAILABLE


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


HEALTH_DEGRADED_EXAMPLE = HealthResponse(
    status='degraded',
    version='0.1.0',
    uptime_sec=1324,
    checks=HealthChecks(
        db=DbCheck(
            status='error',
            reason='db_unavailable',
            detail=DB_DETAIL_UNAVAILABLE,
        )
    ),
).model_dump()

HEALTH_OK_EXAMPLE = HealthResponse(
    status='ok',
    version='0.1.0',
    uptime_sec=1234,
    checks=HealthChecks(
        db=DbCheck(
            status='ok',
            latency_ms=1,
        )
    ),
).model_dump()
