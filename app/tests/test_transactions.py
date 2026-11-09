import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.connection import get_db
from app.main import app
from app.models import (
    Account,
    Complaint,
    ComplaintCategory,
    ComplaintPriority,
    ComplaintStatus,
    ComplaintStatusEvent,
    Customer,
)


@pytest.fixture
def client_and_session_factory():
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
    with TestClient(app) as test_client:
        yield test_client, session_factory
    app.dependency_overrides.clear()
    app.dependency_overrides.update(previous_overrides)
    engine.dispose()


def create_customer_and_account(client):
    customer_response = client.post(
        "/customers",
        json={"name": "Test Customer", "email": "transaction-test@example.com"},
    )
    assert customer_response.status_code == 201
    customer_id = customer_response.json()["customer_id"]

    account_response = client.post(
        "/accounts",
        json={"customer_id": customer_id, "account_type": "CHECKING"},
    )
    assert account_response.status_code == 201
    return customer_id, account_response.json()["account_id"]


def complaint_payload(customer_id, account_id):
    return {
        "customer_id": customer_id,
        "account_id": account_id,
        "category": ComplaintCategory.BILLING.value,
        "priority": ComplaintPriority.LOW.value,
        "description": "Transaction boundary test",
    }


def test_complaint_and_initial_status_event_commit_together(
    client_and_session_factory,
):
    client, session_factory = client_and_session_factory
    customer_id, account_id = create_customer_and_account(client)

    response = client.post(
        "/complaints",
        json=complaint_payload(customer_id, account_id),
    )

    assert response.status_code == 201
    with session_factory() as db:
        complaint = db.query(Complaint).one()
        event_record = db.query(ComplaintStatusEvent).one()
        assert event_record.complaint_id == complaint.complaint_id
        assert event_record.previous_status is None
        assert event_record.new_status == ComplaintStatus.SUBMITTED


def test_status_event_insert_failure_rolls_back_complaint(
    client_and_session_factory,
):
    client, session_factory = client_and_session_factory
    customer_id, account_id = create_customer_and_account(client)

    def fail_status_event_insert(mapper, connection, target):
        raise SQLAlchemyError("Injected status-event insert failure")

    event.listen(ComplaintStatusEvent, "before_insert", fail_status_event_insert)
    try:
        response = client.post(
            "/complaints",
            json=complaint_payload(customer_id, account_id),
        )
    finally:
        event.remove(ComplaintStatusEvent, "before_insert", fail_status_event_insert)

    assert response.status_code == 500
    with session_factory() as db:
        assert db.query(Complaint).count() == 0
        assert db.query(ComplaintStatusEvent).count() == 0


def test_repeated_create_request_creates_separate_complaints(
    client_and_session_factory,
):
    client, session_factory = client_and_session_factory
    customer_id, account_id = create_customer_and_account(client)
    payload = complaint_payload(customer_id, account_id)

    first_response = client.post("/complaints", json=payload)
    second_response = client.post("/complaints", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert (
        first_response.json()["complaint_id"]
        != second_response.json()["complaint_id"]
    )
    with session_factory() as db:
        assert db.query(Complaint).count() == 2
        assert db.query(ComplaintStatusEvent).count() == 2