import json
import logging
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.connection import get_db
from app.core.logging_config import SafeJsonFormatter
from app.main import app


@pytest.fixture
def api_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
    app.dependency_overrides.clear()
    app.dependency_overrides.update(previous_overrides)
    engine.dispose()


@pytest.fixture
def captured_api_logs():
    records = []

    class CaptureHandler(logging.Handler):
        def emit(self, record):
            records.append(record)

    logger = logging.getLogger("banking_api")
    handler = CaptureHandler()
    logger.addHandler(handler)
    try:
        yield records
    finally:
        logger.removeHandler(handler)


def assert_correlated_error(response, records, status_code, error_code):
    assert response.status_code == status_code
    body = response.json()
    assert body["code"] == error_code
    assert body["correlation_id"] == response.headers["X-Correlation-ID"]

    log_record = records[-1]
    assert log_record.correlation_id == body["correlation_id"]
    assert log_record.status_code == status_code
    assert log_record.outcome == "error"
    assert log_record.operation
    assert log_record.duration_ms >= 0
    structured = json.loads(SafeJsonFormatter().format(log_record))
    assert {
        "timestamp",
        "level",
        "correlation_id",
        "operation",
        "outcome",
        "duration_ms",
    }.issubset(structured)
    assert structured["correlation_id"] == body["correlation_id"]
    return body


def test_missing_required_fields_return_structured_422(
    api_client,
    captured_api_logs,
):
    response = api_client.post(
        "/complaints",
        json={"customer_id": 1},
        headers={"X-Correlation-ID": "11111111-1111-4111-8111-111111111111"},
    )

    body = assert_correlated_error(
        response,
        captured_api_logs,
        422,
        "VALIDATION_ERROR",
    )
    supplied_id = "11111111-1111-4111-8111-111111111111"
    assert body["correlation_id"] != supplied_id
    assert str(UUID(body["correlation_id"])) == body["correlation_id"]
    assert body["message"] == "Request validation failed"


def test_invalid_field_value_returns_structured_422(
    api_client,
    captured_api_logs,
):
    response = api_client.post(
        "/complaints",
        json={
            "customer_id": "not-an-integer",
            "account_id": 1,
            "category": "NOT_A_CATEGORY",
            "priority": "LOW",
            "description": "Sensitive complaint narrative",
        },
        headers={"X-Correlation-ID": "22222222-2222-4222-8222-222222222222"},
    )

    assert_correlated_error(
        response,
        captured_api_logs,
        422,
        "VALIDATION_ERROR",
    )
    assert "Sensitive complaint narrative" not in response.text


def test_unavailable_database_returns_safe_structured_503(
    api_client,
    captured_api_logs,
):
    class UnavailableDatabase:
        def query(self, _model):
            del _model
            raise OperationalError(
                "SELECT customer",
                {},
                RuntimeError("database password must not be exposed"),
            )

    def unavailable_database():
        return UnavailableDatabase()

    app.dependency_overrides[get_db] = unavailable_database
    response = api_client.get(
        "/customers",
        headers={"X-Correlation-ID": "33333333-3333-4333-8333-333333333333"},
    )

    assert_correlated_error(
        response,
        captured_api_logs,
        503,
        "DEPENDENCY_UNAVAILABLE",
    )
    assert "password" not in response.text.lower()
    assert "Traceback" not in response.text
    assert "password" not in json.dumps(captured_api_logs[-1].__dict__).lower()


def test_unexpected_error_returns_safe_correlated_500(
    api_client,
    captured_api_logs,
):
    class UnexpectedDatabase:
        def query(self, _model):
            del _model
            raise RuntimeError("Sensitive complaint narrative must not be exposed")

    def unexpected_failure():
        return UnexpectedDatabase()

    app.dependency_overrides[get_db] = unexpected_failure
    response = api_client.get(
        "/customers",
        headers={"X-Correlation-ID": "44444444-4444-4444-8444-444444444444"},
    )

    assert_correlated_error(
        response,
        captured_api_logs,
        500,
        "INTERNAL_ERROR",
    )
    body = response.json()
    assert body["message"] == "An unexpected error occurred"
    assert "Sensitive complaint narrative" not in response.text
    assert "Traceback" not in response.text
    assert "Sensitive complaint narrative" not in json.dumps(
        captured_api_logs[-1].__dict__,
        default=str,
    )


def test_invalid_correlation_id_is_replaced(api_client):
    response = api_client.get(
        "/health/live",
        headers={"X-Correlation-ID": "bad id\r\nforged"},
    )

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] != "bad id\r\nforged"
    assert len(response.headers["X-Correlation-ID"]) == 36


def test_invalid_status_transition_uses_catalog_error(
    api_client,
    captured_api_logs,
):
    customer = api_client.post(
        "/customers",
        json={"name": "Status Test", "email": "status-test@example.com"},
    ).json()
    account = api_client.post(
        "/accounts",
        json={"customer_id": customer["customer_id"], "account_type": "CHECKING"},
    ).json()
    complaint = api_client.post(
        "/complaints",
        json={
            "customer_id": customer["customer_id"],
            "account_id": account["account_id"],
            "category": "BILLING",
            "priority": "LOW",
            "description": "Status transition test",
        },
    ).json()

    response = api_client.patch(
        f"/complaints/{complaint['complaint_id']}/status",
        json={"new_status": "RESOLVED", "event_id": 1001},
    )

    body = assert_correlated_error(
        response,
        captured_api_logs,
        409,
        "INVALID_STATUS_TRANSITION",
    )
    assert body["message"] == "Invalid complaint status transition"


def test_missing_complaint_uses_catalog_error(api_client, captured_api_logs):
    response = api_client.get("/complaints/999")

    body = assert_correlated_error(
        response,
        captured_api_logs,
        404,
        "COMPLAINT_NOT_FOUND",
    )
    assert body["message"] == "Complaint not found"
