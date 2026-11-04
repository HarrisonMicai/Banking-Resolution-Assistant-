import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.models import (
    Account,
    Complaint,
    ComplaintCategory,
    ComplaintPriority,
    ComplaintStatusEvent,
    Customer,
)
from app.repositories.customer_repository import CustomerRepository
from app.services.complaint_service import ComplaintService
from app.services.exceptions import ComplaintCreationError


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with session_factory() as db:
        yield db
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_customer_repository_get_by_id(db_session):
    customer = Customer(name="Jane Doe", email="jane.doe@example.com")
    db_session.add(customer)
    db_session.commit()

    repository = CustomerRepository()
    assert repository.get_by_id(db_session, customer.customer_id) is customer
    assert repository.get_by_id(db_session, 999999) is None


def test_complaint_service_rolls_back_failure_creating_initial_event(db_session):
    customer = Customer(name="Jane Doe", email="jane.doe@example.com")
    db_session.add(customer)
    db_session.flush()
    account = Account(
        customer_id=customer.customer_id,
        account_type="CHECKING",
        balance=0,
    )
    db_session.add(account)
    db_session.commit()

    def fail_event_insert(mapper, connection, target):
        del mapper, connection, target
        raise SQLAlchemyError("Injected status-event insert failure")

    event.listen(ComplaintStatusEvent, "before_insert", fail_event_insert)
    try:
        with pytest.raises(ComplaintCreationError):
            ComplaintService().create_complaint(
                db_session,
                customer_id=customer.customer_id,
                account_id=account.account_id,
                category=ComplaintCategory.BILLING,
                priority=ComplaintPriority.LOW,
                description="Injected persistence failure",
            )
    finally:
        event.remove(ComplaintStatusEvent, "before_insert", fail_event_insert)

    assert db_session.query(Complaint).count() == 0
    assert db_session.query(ComplaintStatusEvent).count() == 0
