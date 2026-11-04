from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from fastapi.testclient import TestClient

from app.database import connection
from app.main import app


def test_readiness_checks_the_api_database_engine(monkeypatch):
    api_engine = create_engine("sqlite://")
    monkeypatch.setattr(connection, "engine", api_engine)

    with TestClient(app) as client:
        response = client.get("/health/ready")

    api_engine.dispose()
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "connected"}


def test_readiness_reports_unavailable_api_database(monkeypatch):
    class UnavailableEngine:
        def connect(self):
            raise OperationalError(
                "SELECT 1",
                {},
                RuntimeError("database unavailable"),
            )

    monkeypatch.setattr(connection, "engine", UnavailableEngine())

    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not ready",
        "database": "disconnected",
    }
