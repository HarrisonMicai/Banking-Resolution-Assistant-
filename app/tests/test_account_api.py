import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.connection import get_db
from app.main import app


@pytest.fixture
def client():
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

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


def test_create_account_then_complaint(client):
    customer_response = client.post(
        "/customers",
        json={"name": "Micai", "email": "micai@example.com"},
    )
    customer_id = customer_response.json()["customer_id"]

    account_response = client.post(
        "/accounts",
        json={"customer_id": customer_id, "account_type": "CHECKING"},
    )

    assert account_response.status_code == 201
    account = account_response.json()
    assert account["customer_id"] == customer_id
    assert account["balance"] == 0.0

    complaint_response = client.post(
        "/complaints",
        json={
            "customer_id": customer_id,
            "account_id": account["account_id"],
            "category": "BILLING",
            "priority": "LOW",
            "description": "Incorrect fee on my account",
        },
    )

    assert complaint_response.status_code == 201
    assert complaint_response.json()["customer_id"] == customer_id
    assert complaint_response.json()["account_id"] == account["account_id"]


def test_create_account_requires_existing_customer(client):
    response = client.post(
        "/accounts",
        json={"customer_id": 999, "account_type": "CHECKING"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Customer not found"}
