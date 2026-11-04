from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Account
from app.repositories.account_repository import AccountRepository
from app.repositories.customer_repository import CustomerRepository
from app.services.exceptions import (
    CustomerNotFoundError,
    ResourceConflictError,
)


class AccountService:
    def __init__(
        self,
        account_repo: AccountRepository | None = None,
        customer_repo: CustomerRepository | None = None,
    ):
        self.account_repo = (
            account_repo if account_repo is not None else AccountRepository()
        )
        self.customer_repo = (
            customer_repo if customer_repo is not None else CustomerRepository()
        )

    def create_account(
        self,
        db: Session,
        customer_id: int,
        account_type: str,
        balance: float,
    ) -> Account:
        if self.customer_repo.get_by_id(db, customer_id) is None:
            raise CustomerNotFoundError(
                f"Customer with ID {customer_id} not found."
            )

        try:
            account = self.account_repo.create(
                db,
                customer_id=customer_id,
                account_type=account_type,
                balance=balance,
            )
            db.commit()
            db.refresh(account)
        except IntegrityError as exc:
            db.rollback()
            raise ResourceConflictError(
                "The request conflicts with the current resource state"
            ) from exc
        except Exception:
            db.rollback()
            raise
        return account
