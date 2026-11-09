import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.connection import get_db
from app.main import app
from app.models import Account, Customer


@pytest.fixture
def integration_environment():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    with session_factory() as db:
        customer = Customer(name="Integration Customer", email="integration@example.com")
        db.add(customer)
        db.flush()
        account = Account(
            customer_id=customer.customer_id,
            account_type="CHECKING",
            balance=125.0,
        )
        db.add(account)
        db.commit()
        customer_id = customer.customer_id
        account_id = account.account_id

    def override_get_db():
        with session_factory() as db:
            yield db

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            yield {
                "client": client,
                "session_factory": session_factory,
                "customer_id": customer_id,
                "account_id": account_id,
            }
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
