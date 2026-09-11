import asyncio
import time

from fastapi import APIRouter, Response, status
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from app.config import settings
from app.constants import (
    DB_CHECK_TIMEOUT_S,
    DB_DETAIL_LOCKED,
    DB_DETAIL_TIMEOUT,
    DB_DETAIL_UNAVAILABLE,
)
from app.database import async_engine, check_database_connection
from app.schemas.health import DbCheck, HealthChecks, HealthResponse

# Время запуска приложения. (момент импорта модуля)
_APP_START = time.monotonic()

router = APIRouter()


def _get_app_uptime() -> int:
    """Возвращает время работы приложения в секундах."""
    return int(time.monotonic() - _APP_START)


@router.get(
    '/health',
    response_model=HealthResponse,
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            'model': HealthResponse,
            'description': 'Приложение работает, БД недоступна',
        }
    },
)
async def health_check(response: Response) -> HealthResponse:
    """Проверка состояния приложения.

    - Возвращает статус 200 и время его работы.

    - Возвращает статус 503 и причину ошибки, если соединение с БД отсутствует.
    """
    # Часы высокого разрешения (monotic на Windows дает шаг 15.6 мс)
    start_time = time.perf_counter()
    try:
        await asyncio.wait_for(
            check_database_connection(async_engine), timeout=DB_CHECK_TIMEOUT_S
        )
        is_ok, reason, detail = True, None, None
    except TimeoutError:
        is_ok, reason, detail = False, 'db_timeout', DB_DETAIL_TIMEOUT
    except OperationalError as exc:
        if 'locked' in str(exc).lower():
            is_ok, reason, detail = False, 'db_locked', DB_DETAIL_LOCKED
        else:
            is_ok, reason, detail = (
                False,
                'db_unavailable',
                DB_DETAIL_UNAVAILABLE,
            )
    except SQLAlchemyError:
        is_ok, reason, detail = False, 'db_unavailable', DB_DETAIL_UNAVAILABLE

    response.headers['Cache-Control'] = 'no-store'
    response.status_code = (
        status.HTTP_200_OK if is_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    # при ошибке замер бессмыслен: это был бы таймаут, а не время ответа БД
    latency_ms = (
        int((time.perf_counter() - start_time) * 1000) if is_ok else None
    )
    return HealthResponse(
        status='ok' if is_ok else 'degraded',
        version=settings.app_version,
        uptime_sec=_get_app_uptime(),
        checks=HealthChecks(
            db=DbCheck(
                status='ok' if is_ok else 'error',
                latency_ms=latency_ms,
                reason=reason,
                detail=detail,
            )
        ),
    )
