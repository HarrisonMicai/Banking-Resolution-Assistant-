from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, OperationalError

from app.database.connection import get_db
from app.main import app
from app.models import (
    Complaint,
    ComplaintCategory,
    ComplaintPriority,
    ComplaintStatus,
    ComplaintStatusEvent,
    Customer,
)


def assert_correlation_id(response, expected_id):
    assert response.headers["X-Correlation-ID"] == expected_id
    if response.status_code >= 400:
        assert response.json()["correlation_id"] == expected_id


def complaint_payload(customer_id, account_id):
    return {
        "customer_id": customer_id,
        "account_id": account_id,
        "category": ComplaintCategory.BILLING.value,
        "priority": ComplaintPriority.LOW.value,
        "description": "Integration-test complaint",
    }


def create_complaint(client, customer_id, account_id):
    response = client.post(
        "/complaints",
        json=complaint_payload(customer_id, account_id),
    )
    assert response.status_code == 201
    return response.json()


def test_customer_lookup_returns_customer_and_not_found(
    integration_environment,
):
    client = integration_environment["client"]
    customer_id = integration_environment["customer_id"]
    session_factory = integration_environment["session_factory"]

    response = client.get(
        f"/customers/{customer_id}",
        headers={"X-Correlation-ID": "10000000-0000-4000-8000-000000000001"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "customer_id": customer_id,
        "name": "Integration Customer",
        "email": "integration@example.com",
    }

    missing_response = client.get(
        "/customers/999999",
        headers={"X-Correlation-ID": "10000000-0000-4000-8000-000000000002"},
    )
    assert missing_response.status_code == 404
    assert missing_response.json()["code"] == "CUSTOMER_NOT_FOUND"
    assert_correlation_id(
        missing_response,
        "10000000-0000-4000-8000-000000000002",
    )

    with session_factory() as db:
        assert db.query(Customer).count() == 1


def test_complaint_creation_persists_status_event_and_invalid_input_is_422(
    integration_environment,
):
    client = integration_environment["client"]
    customer_id = integration_environment["customer_id"]
    account_id = integration_environment["account_id"]
    session_factory = integration_environment["session_factory"]

    response = client.post(
        "/complaints",
        json=complaint_payload(customer_id, account_id),
        headers={"X-Correlation-ID": "20000000-0000-4000-8000-000000000001"},
    )

    assert response.status_code == 201
    complaint_body = response.json()
    assert complaint_body["customer_id"] == customer_id
    assert complaint_body["account_id"] == account_id
    assert complaint_body["status"] == ComplaintStatus.SUBMITTED.value
    assert_correlation_id(
        response,
        "20000000-0000-4000-8000-000000000001",
    )

    invalid_payload = complaint_payload(customer_id, account_id)
    invalid_payload.pop("priority")
    invalid_response = client.post("/complaints", json=invalid_payload)

    assert invalid_response.status_code == 422
    assert invalid_response.json()["code"] == "VALIDATION_ERROR"
    assert invalid_response.json()["message"] == "Request validation failed"
    assert invalid_response.headers["X-Correlation-ID"]

    with session_factory() as db:
        complaints = db.query(Complaint).all()
        events = db.query(ComplaintStatusEvent).all()
        assert len(complaints) == 1
        assert len(events) == 1
        assert events[0].complaint_id == complaint_body["complaint_id"]
        assert events[0].new_status == ComplaintStatus.SUBMITTED


def test_valid_status_update_persists_status_and_history(
    integration_environment,
):
    client = integration_environment["client"]
    customer_id = integration_environment["customer_id"]
    account_id = integration_environment["account_id"]
    session_factory = integration_environment["session_factory"]
    complaint = create_complaint(client, customer_id, account_id)

    response = client.patch(
        f"/complaints/{complaint['complaint_id']}/status",
        json={
            "new_status": ComplaintStatus.UNDER_REVIEW.value,
            "event_id": 7001,
            "notes": "Integration review event",
        },
        headers={"X-Correlation-ID": "30000000-0000-4000-8000-000000000001"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == ComplaintStatus.UNDER_REVIEW.value
    assert_correlation_id(
        response,
        "30000000-0000-4000-8000-000000000001",
    )

    with session_factory() as db:
        persisted = db.get(Complaint, complaint["complaint_id"])
        events = (
            db.query(ComplaintStatusEvent)
            .filter(
                ComplaintStatusEvent.complaint_id
                == complaint["complaint_id"]
            )
            .order_by(ComplaintStatusEvent.event_id)
            .all()
        )
        assert persisted.status == ComplaintStatus.UNDER_REVIEW
        assert len(events) == 2
        assert events[1].previous_status == ComplaintStatus.SUBMITTED
        assert events[1].new_status == ComplaintStatus.UNDER_REVIEW
        assert events[1].event_id == 7001
        assert events[1].notes == "Integration review event"


def test_invalid_status_update_returns_409_without_database_changes(
    integration_environment,
):
    client = integration_environment["client"]
    customer_id = integration_environment["customer_id"]
    account_id = integration_environment["account_id"]
    session_factory = integration_environment["session_factory"]
    complaint = create_complaint(client, customer_id, account_id)

    response = client.patch(
        f"/complaints/{complaint['complaint_id']}/status",
        json={
            "new_status": ComplaintStatus.RESOLVED.value,
            "event_id": 7002,
        },
        headers={"X-Correlation-ID": "40000000-0000-4000-8000-000000000001"},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "INVALID_STATUS_TRANSITION"
    assert_correlation_id(
        response,
        "40000000-0000-4000-8000-000000000001",
    )

    with session_factory() as db:
        persisted = db.get(Complaint, complaint["complaint_id"])
        events = (
            db.query(ComplaintStatusEvent)
            .filter(
                ComplaintStatusEvent.complaint_id
                == complaint["complaint_id"]
            )
            .all()
        )
        assert persisted.status == ComplaintStatus.SUBMITTED
        assert len(events) == 1
        assert events[0].new_status == ComplaintStatus.SUBMITTED


def test_initial_event_insert_failure_rolls_back_complaint(
    integration_environment,
):
    client = integration_environment["client"]
    customer_id = integration_environment["customer_id"]
    account_id = integration_environment["account_id"]
    session_factory = integration_environment["session_factory"]

    def fail_event_insert(mapper, connection, target):
        del mapper, connection, target
        raise IntegrityError(
            "Injected initial status-event failure",
            {},
            RuntimeError("test failure"),
        )

    event.listen(ComplaintStatusEvent, "before_insert", fail_event_insert)
    try:
        response = client.post(
            "/complaints",
            json=complaint_payload(customer_id, account_id),
            headers={"X-Correlation-ID": "50000000-0000-4000-8000-000000000001"},
        )
    finally:
        event.remove(ComplaintStatusEvent, "before_insert", fail_event_insert)

    assert response.status_code == 409
    assert response.json()["code"] == "CONFLICT"
    assert_correlation_id(
        response,
        "50000000-0000-4000-8000-000000000001",
    )

    with session_factory() as db:
        assert db.query(Complaint).count() == 0
        assert db.query(ComplaintStatusEvent).count() == 0


def test_unavailable_database_returns_safe_error_and_correlation_id(
    integration_environment,
):
    client = integration_environment["client"]
    session_factory = integration_environment["session_factory"]
    original_dependency = app.dependency_overrides[get_db]

    class UnavailableSession:
        def query(self, model):
            del model
            raise OperationalError(
                "SELECT customers",
                {},
                RuntimeError("database secret must not appear in the response"),
            )

    def unavailable_database():
        return UnavailableSession()

    try:
        app.dependency_overrides[get_db] = unavailable_database
        response = client.get(
            "/customers",
            headers={"X-Correlation-ID": "60000000-0000-4000-8000-000000000001"},
        )
    finally:
        app.dependency_overrides[get_db] = original_dependency

    assert response.status_code == 503
    assert response.json()["code"] == "DEPENDENCY_UNAVAILABLE"
    assert "secret" not in response.text.lower()
    assert "Traceback" not in response.text
    assert_correlation_id(
        response,
        "60000000-0000-4000-8000-000000000001",
    )

    with session_factory() as db:
        assert db.query(Customer).count() == 1
