import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    """Тестовый HTTP-клиент."""
    return TestClient(app)
