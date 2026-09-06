from typing import Literal

from pydantic import BaseModel


class DbCheck(BaseModel):
    """Результат проверки одной зависимости."""

    status: Literal['ok', 'error']
    latency_ms: int
    reason: str | None = None
    detail: str | None = None


class HealthChecks(BaseModel):
    """Объект checks: ключ на каждую зависимость."""

    db: DbCheck


class HealthResponse(BaseModel):
    """Единая схема ответа /health для 200 и 503."""

    status: Literal['ok', 'degraded']
    version: str
    uptime_sec: int
    checks: HealthChecks
