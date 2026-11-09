from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Customer
from app.repositories.customer_repository import CustomerRepository
from app.services.exceptions import (
    CustomerNotFoundError,
    ResourceConflictError,
)


class CustomerService:
    def __init__(self, customer_repo: CustomerRepository | None = None):
        self.customer_repo = (
            customer_repo if customer_repo is not None else CustomerRepository()
        )

    def create_customer(self, db: Session, name: str, email: str) -> Customer:
        try:
            customer = self.customer_repo.create(db, name=name, email=email)
            db.commit()
            db.refresh(customer)
        except IntegrityError as exc:
            db.rollback()
            raise ResourceConflictError(
                "A customer with this email already exists"
            ) from exc
        except Exception:
            db.rollback()
            raise
        return customer

    def list_customers(self, db: Session) -> list[Customer]:
        return self.customer_repo.get_all(db)

    def get_customer(self, db: Session, customer_id: int) -> Customer:
        customer = self.customer_repo.get_by_id(db, customer_id)
        if customer is None:
            raise CustomerNotFoundError(
                f"Customer with ID {customer_id} not found."
            )
        return customer

    def update_customer(
        self,
        db: Session,
        customer_id: int,
        updates: dict[str, str | None],
    ) -> Customer:
        customer = self.get_customer(db, customer_id)
        try:
            self.customer_repo.update(db, customer, updates)
            db.commit()
            db.refresh(customer)
        except IntegrityError as exc:
            db.rollback()
            raise ResourceConflictError(
                "A customer with this email already exists"
            ) from exc
        except Exception:
            db.rollback()
            raise
        return customer

    def delete_customer(self, db: Session, customer_id: int) -> None:
        customer = self.get_customer(db, customer_id)
        if self.customer_repo.has_related_records(db, customer_id):
            raise ResourceConflictError(
                "Customer cannot be deleted while related records exist"
            )

        try:
            self.customer_repo.delete(db, customer)
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise ResourceConflictError(
                "Customer cannot be deleted while related records exist"
            ) from exc
        except Exception:
            db.rollback()
            raise
