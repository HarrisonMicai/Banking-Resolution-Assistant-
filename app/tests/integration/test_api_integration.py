from datetime import datetime
from uuid import UUID

from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, OperationalError

from app.database.connection import get_db
from app.main import app
from app.models import (
    Account,
    Complaint,
    ComplaintCategory,
    ComplaintPriority,
    ComplaintSoftDeletion,
    ComplaintStatus,
    ComplaintStatusEvent,
    Customer,
)


def assert_server_generated_correlation_id(response, supplied_id=None):
    correlation_id = response.headers["X-Correlation-ID"]
    parsed_id = UUID(correlation_id)

    assert str(parsed_id) == correlation_id
    if supplied_id is not None:
        assert correlation_id != supplied_id
    if response.status_code >= 400:
        assert response.json()["correlation_id"] == correlation_id


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

    supplied_id = "10000000-0000-4000-8000-000000000001"
    response = client.get(
        f"/customers/{customer_id}",
        headers={"X-Correlation-ID": supplied_id},
    )

    assert response.status_code == 200
    assert response.json() == {
        "customer_id": customer_id,
        "name": "Integration Customer",
        "email": "integration@example.com",
    }
    assert_server_generated_correlation_id(response, supplied_id)

    missing_supplied_id = "10000000-0000-4000-8000-000000000002"
    missing_response = client.get(
        "/customers/999999",
        headers={"X-Correlation-ID": missing_supplied_id},
    )
    assert missing_response.status_code == 404
    assert missing_response.json()["code"] == "CUSTOMER_NOT_FOUND"
    assert_server_generated_correlation_id(
        missing_response,
        missing_supplied_id,
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

    supplied_id = "20000000-0000-4000-8000-000000000001"
    response = client.post(
        "/complaints",
        json=complaint_payload(customer_id, account_id),
        headers={"X-Correlation-ID": supplied_id},
    )

    assert response.status_code == 201
    complaint_body = response.json()
    assert complaint_body["customer_id"] == customer_id
    assert complaint_body["account_id"] == account_id
    assert complaint_body["status"] == ComplaintStatus.SUBMITTED.value
    assert_server_generated_correlation_id(response, supplied_id)

    invalid_payload = complaint_payload(customer_id, account_id)
    invalid_payload.pop("priority")
    invalid_response = client.post("/complaints", json=invalid_payload)

    assert invalid_response.status_code == 422
    assert invalid_response.json()["code"] == "VALIDATION_ERROR"
    assert invalid_response.json()["message"] == "Request validation failed"
    assert_server_generated_correlation_id(invalid_response)

    with session_factory() as db:
        complaints = db.query(Complaint).all()
        events = db.query(ComplaintStatusEvent).all()
        assert len(complaints) == 1
        assert len(events) == 1
        assert events[0].complaint_id == complaint_body["complaint_id"]
        assert events[0].new_status == ComplaintStatus.SUBMITTED


def test_list_complaints_filters_by_customer_and_account(
    integration_environment,
):
    client = integration_environment["client"]
    customer_id = integration_environment["customer_id"]
    first_account_id = integration_environment["account_id"]

    first_complaint = create_complaint(client, customer_id, first_account_id)

    second_account_response = client.post(
        "/accounts",
        json={"customer_id": customer_id, "account_type": "SAVINGS"},
    )
    assert second_account_response.status_code == 201
    second_account_id = second_account_response.json()["account_id"]
    second_complaint = create_complaint(client, customer_id, second_account_id)

    customer_response = client.get(
        "/complaints",
        params={"customer_id": customer_id},
    )
    assert customer_response.status_code == 200
    assert {
        complaint["complaint_id"] for complaint in customer_response.json()
    } == {
        first_complaint["complaint_id"],
        second_complaint["complaint_id"],
    }

    account_response = client.get(
        "/complaints",
        params={"account_id": second_account_id},
    )
    assert account_response.status_code == 200
    assert [
        complaint["complaint_id"] for complaint in account_response.json()
    ] == [second_complaint["complaint_id"]]

    combined_response = client.get(
        "/complaints",
        params={
            "customer_id": customer_id,
            "account_id": first_account_id,
        },
    )
    assert combined_response.status_code == 200
    assert [
        complaint["complaint_id"] for complaint in combined_response.json()
    ] == [first_complaint["complaint_id"]]


def test_complaint_description_is_required_and_cannot_be_blank(
    integration_environment,
):
    client = integration_environment["client"]
    customer_id = integration_environment["customer_id"]
    account_id = integration_environment["account_id"]

    missing_description = complaint_payload(customer_id, account_id)
    missing_description.pop("description")
    blank_descriptions = [
        missing_description,
        complaint_payload(customer_id, account_id) | {"description": ""},
        complaint_payload(customer_id, account_id) | {"description": "   "},
    ]

    for payload in blank_descriptions:
        response = client.post("/complaints", json=payload)

        assert response.status_code == 422
        assert response.json()["code"] == "VALIDATION_ERROR"
        assert_server_generated_correlation_id(response)


def test_valid_status_update_persists_status_and_history(
    integration_environment,
):
    client = integration_environment["client"]
    customer_id = integration_environment["customer_id"]
    account_id = integration_environment["account_id"]
    session_factory = integration_environment["session_factory"]
    complaint = create_complaint(client, customer_id, account_id)

    supplied_id = "30000000-0000-4000-8000-000000000001"
    response = client.patch(
        f"/complaints/{complaint['complaint_id']}/status",
        json={
            "new_status": ComplaintStatus.UNDER_REVIEW.value,
            "event_id": 7001,
            "notes": "Integration review event",
        },
        headers={"X-Correlation-ID": supplied_id},
    )

    assert response.status_code == 200
    assert response.json()["status"] == ComplaintStatus.UNDER_REVIEW.value
    assert_server_generated_correlation_id(response, supplied_id)

    history_response = client.get(
        f"/complaints/{complaint['complaint_id']}/status-history"
    )
    assert history_response.status_code == 200
    history = history_response.json()
    assert len(history) == 2
    assert history[0]["previous_status"] is None
    assert history[0]["new_status"] == ComplaintStatus.SUBMITTED.value
    assert history[0]["notes"] is None
    assert history[1]["previous_status"] == ComplaintStatus.SUBMITTED.value
    assert history[1]["new_status"] == ComplaintStatus.UNDER_REVIEW.value
    assert history[1]["notes"] == "Integration review event"
    assert history[1]["event_id"] == 7001
    assert datetime.fromisoformat(history[0]["timestamp"])
    assert datetime.fromisoformat(history[1]["timestamp"])
    assert set(history[1]) == {
        "event_id",
        "previous_status",
        "new_status",
        "timestamp",
        "notes",
    }

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


def test_missing_complaint_status_history_returns_not_found(
        integration_environment,
):
        response = integration_environment["client"].get(
            "/complaints/999999/status-history"
        )

        assert response.status_code == 404
        assert response.json()["code"] == "COMPLAINT_NOT_FOUND"


def test_invalid_status_update_returns_409_without_database_changes(
    integration_environment,
):
    client = integration_environment["client"]
    customer_id = integration_environment["customer_id"]
    account_id = integration_environment["account_id"]
    session_factory = integration_environment["session_factory"]
    complaint = create_complaint(client, customer_id, account_id)

    supplied_id = "40000000-0000-4000-8000-000000000001"
    response = client.patch(
        f"/complaints/{complaint['complaint_id']}/status",
        json={
            "new_status": ComplaintStatus.RESOLVED.value,
            "event_id": 7002,
        },
        headers={"X-Correlation-ID": supplied_id},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "INVALID_STATUS_TRANSITION"
    assert_server_generated_correlation_id(response, supplied_id)

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
        supplied_id = "50000000-0000-4000-8000-000000000001"
        response = client.post(
            "/complaints",
            json=complaint_payload(customer_id, account_id),
            headers={"X-Correlation-ID": supplied_id},
        )
    finally:
        event.remove(ComplaintStatusEvent, "before_insert", fail_event_insert)

    assert response.status_code == 409
    assert response.json()["code"] == "CONFLICT"
    assert_server_generated_correlation_id(response, supplied_id)

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

    supplied_id = "60000000-0000-4000-8000-000000000001"
    try:
        app.dependency_overrides[get_db] = unavailable_database
        response = client.get(
            "/customers",
            headers={"X-Correlation-ID": supplied_id},
        )
    finally:
        app.dependency_overrides[get_db] = original_dependency

    assert response.status_code == 503
    assert response.json()["code"] == "DEPENDENCY_UNAVAILABLE"
    assert "secret" not in response.text.lower()
    assert "Traceback" not in response.text
    assert_server_generated_correlation_id(response, supplied_id)

    with session_factory() as db:
        assert db.query(Customer).count() == 1


def test_delete_complaint_hides_record_but_preserves_history_and_actor(
    integration_environment,
):
    client = integration_environment["client"]
    customer_id = integration_environment["customer_id"]
    account_id = integration_environment["account_id"]
    session_factory = integration_environment["session_factory"]
    complaint = create_complaint(client, customer_id, account_id)
    complaint_id = complaint["complaint_id"]

    response = client.delete(f"/complaints/{complaint_id}")

    assert response.status_code == 204
    with session_factory() as db:
        assert db.get(Complaint, complaint_id) is not None
        assert db.query(ComplaintSoftDeletion).filter_by(
            complaint_id=complaint_id
        ).one().deleted_by == "unauthenticated"
        assert (
            db.query(ComplaintStatusEvent)
            .filter(ComplaintStatusEvent.complaint_id == complaint_id)
            .count()
            == 1
        )
        deletion = db.query(ComplaintSoftDeletion).filter_by(
            complaint_id=complaint_id
        ).one()
        assert deletion.deleted_by == "unauthenticated"
        assert deletion.deleted_at is not None

    missing_response = client.get(f"/complaints/{complaint_id}")
    assert missing_response.status_code == 404
    assert missing_response.json()["code"] == "COMPLAINT_NOT_FOUND"
    missing_response = client.delete("/complaints/999999")
    assert missing_response.status_code == 404
    assert missing_response.json()["code"] == "COMPLAINT_NOT_FOUND"

    history_response = client.get(
        f"/complaints/{complaint_id}/status-history"
    )
    assert history_response.status_code == 404
    assert history_response.json()["code"] == "COMPLAINT_NOT_FOUND"
    assert client.get("/complaints").json() == []


def test_delete_account_without_complaints(integration_environment):
    client = integration_environment["client"]
    account_id = integration_environment["account_id"]
    session_factory = integration_environment["session_factory"]

    response = client.delete(f"/accounts/{account_id}")

    assert response.status_code == 204
    with session_factory() as db:
        assert db.get(Account, account_id) is None

    missing_response = client.delete("/accounts/999999")
    assert missing_response.status_code == 404
    assert missing_response.json()["code"] == "ACCOUNT_NOT_FOUND"


def test_account_and_customer_deletion_are_blocked_by_related_records(
    integration_environment,
):
    client = integration_environment["client"]
    customer_id = integration_environment["customer_id"]
    account_id = integration_environment["account_id"]
    session_factory = integration_environment["session_factory"]
    complaint = create_complaint(client, customer_id, account_id)

    account_response = client.delete(f"/accounts/{account_id}")
    assert account_response.status_code == 409
    assert account_response.json()["code"] == "CONFLICT"

    customer_response = client.delete(f"/customers/{customer_id}")
    assert customer_response.status_code == 409
    assert customer_response.json()["code"] == "CONFLICT"

    with session_factory() as db:
        assert db.get(Account, account_id) is not None
        assert db.get(Customer, customer_id) is not None
        assert db.get(Complaint, complaint["complaint_id"]) is not None