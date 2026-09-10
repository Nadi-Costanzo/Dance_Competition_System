import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine

from app.config import settings
from app.constants import API_PREFIX
from app.schemas.health import HealthResponse


def test_health_check_returns_200(client: TestClient) -> None:
    """Проверяет, что get.health возвращает 200 OK."""
    response = client.get('/api/v1/health')
    data = response.json()
    assert response.status_code == 200
    parsed = HealthResponse.model_validate(data)
    assert parsed.status == 'ok'
    assert parsed.checks.db.status == 'ok'
    assert parsed.checks.db.reason is None
    assert parsed.checks.db.detail is None
    assert parsed.version == settings.app_version


def test_health_check_returns_503_on_db_timeout(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Проверяет, что get.health возвращает 503 при таймауте БД."""

    async def mock_check_database_connection(engine: AsyncEngine) -> None:
        await asyncio.sleep(3)  # больше, чем DB_CHECK_TIMEOUT_S
        raise TimeoutError('DB timeout')

    monkeypatch.setattr(
        'app.api.health.check_database_connection',
        mock_check_database_connection,
    )
    response = client.get('/api/v1/health')
    data = response.json()
    assert response.status_code == 503
    parsed = HealthResponse.model_validate(data)
    assert parsed.status == 'degraded'
    assert parsed.checks.db.status == 'error'
    assert parsed.checks.db.reason == 'db_timeout'
    assert parsed.version == settings.app_version


def test_health_path_uses_configured_prefix(client: TestClient) -> None:
    """Проверяет, что путь зашит в client.get('/api/v1/health')."""
    assert client.get(f'{API_PREFIX}/health').status_code == 200
