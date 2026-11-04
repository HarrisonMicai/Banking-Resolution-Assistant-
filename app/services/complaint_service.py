from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import Complaint, ComplaintCategory, ComplaintPriority, ComplaintStatus
from app.repositories.account_repository import AccountRepository
from app.repositories.complaint_repository import ComplaintRepository
from app.repositories.customer_repository import CustomerRepository
from app.services.exceptions import (
    AccountNotFoundError,
    ComplaintCreationError,
    ComplaintNotFoundError,
    CustomerNotFoundError,
    DependencyUnavailableError,
    InvalidComplaintTransitionError,
    ResourceConflictError,
)


class ComplaintService:
    def __init__(
        self,
        complaint_repo: ComplaintRepository | None = None,
        customer_repo: CustomerRepository | None = None,
        account_repo: AccountRepository | None = None,
    ):
        self.complaint_repo = (
            complaint_repo if complaint_repo is not None else ComplaintRepository()
        )
        self.customer_repo = (
            customer_repo if customer_repo is not None else CustomerRepository()
        )
        self.account_repo = (
            account_repo if account_repo is not None else AccountRepository()
        )

    def create_complaint(
        self,
        db: Session,
        *,
        customer_id: int,
        account_id: int,
        category: ComplaintCategory,
        priority: ComplaintPriority,
        description: str,
    ) -> Complaint:
        customer = self.customer_repo.get_by_id(db, customer_id)
        if customer is None:
            raise CustomerNotFoundError(
                f"Customer with ID {customer_id} not found."
            )

        account = self.account_repo.get_by_id(db, account_id)
        if account is None or account.customer_id != customer_id:
            raise AccountNotFoundError(
                f"Account with ID {account_id} not found for customer "
                f"{customer_id}."
            )

        try:
            complaint = self.complaint_repo.create(
                db,
                customer_id=customer_id,
                account_id=account_id,
                category=category,
                priority=priority,
                description=description,
            )
            db.commit()
            db.refresh(complaint)
        except IntegrityError as exc:
            db.rollback()
            raise ResourceConflictError(
                "Complaint and initial status event could not be saved"
            ) from exc
        except SQLAlchemyError as exc:
            db.rollback()
            raise ComplaintCreationError() from exc
        except Exception:
            db.rollback()
            raise

        return complaint

    def list_complaints(
        self,
        db: Session,
        customer_id: int | None = None,
    ) -> list[Complaint]:
        return self.complaint_repo.get_all(db, customer_id)

    def get_complaint(self, db: Session, complaint_id: int) -> Complaint:
        complaint = self.complaint_repo.get_by_id(db, complaint_id)
        if complaint is None:
            raise ComplaintNotFoundError(
                f"Complaint with ID {complaint_id} not found."
            )
        return complaint

    def progress_complaint_status(
        self,
        db: Session,
        complaint_id: int,
        new_status: ComplaintStatus,
        event_id: int,
        notes: str | None = None,
    ) -> Complaint:
        complaint = self.get_complaint(db, complaint_id)
        try:
            self.complaint_repo.update_status(
                db,
                complaint,
                new_status,
                event_id,
                notes,
            )
        except ValueError as exc:
            db.rollback()
            raise InvalidComplaintTransitionError() from exc

        try:
            db.commit()
            db.refresh(complaint)
        except IntegrityError as exc:
            db.rollback()
            raise ResourceConflictError(
                "The request conflicts with the current resource state"
            ) from exc
        except SQLAlchemyError as exc:
            db.rollback()
            raise DependencyUnavailableError() from exc
        except Exception:
            db.rollback()
            raise

        return complaint
