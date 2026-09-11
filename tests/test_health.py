import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from app.config import settings
from app.constants import API_PREFIX
from app.main import app
from app.schemas.health import HealthResponse


def test_health_check_returns_200(client: TestClient) -> None:
    """Проверяет, что get.health возвращает 200 OK."""
    response = client.get(f'{API_PREFIX}/health')
    data = response.json()
    assert response.status_code == 200
    parsed = HealthResponse.model_validate(data)
    assert parsed.status == 'ok'
    assert parsed.checks.db.status == 'ok'
    assert parsed.checks.db.reason is None
    assert parsed.checks.db.detail is None
    assert parsed.version == settings.app_version


@pytest.mark.parametrize(
    'exception, expected_reason',
    [
        (TimeoutError(), 'db_timeout'),
        (
            OperationalError('', None, Exception('database is locked')),
            'db_locked',
        ),
        (
            OperationalError(
                '', None, Exception('unable to open database file')
            ),
            'db_unavailable',
        ),
        (SQLAlchemyError(), 'db_unavailable'),
    ],
)
def test_health_check_returns_503(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    exception: Exception,
    expected_reason: str,
) -> None:
    """Проверяет get.health (статус 503 при отсутствии соединения с БД)."""

    async def _raise(_engine: AsyncEngine) -> None:
        raise exception

    monkeypatch.setattr(
        'app.api.health.check_database_connection',
        _raise,
    )
    response = client.get(f'{API_PREFIX}/health')
    data = response.json()
    assert response.status_code == 503
    parsed = HealthResponse.model_validate(data)
    assert parsed.status == 'degraded'
    assert parsed.checks.db.status == 'error'
    assert parsed.checks.db.reason == expected_reason
    assert parsed.checks.db.latency_ms is None
    assert parsed.version == settings.app_version


def test_all_api_paths_use_configured_prefix() -> None:
    """Все пути API объявлены под единым префиксом."""
    paths = app.openapi()['paths']
    assert paths
    assert all(path.startswith(API_PREFIX) for path in paths)
