from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Account
from app.repositories.account_repository import AccountRepository
from app.repositories.customer_repository import CustomerRepository
from app.services.exceptions import (
    AccountNotFoundError,
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

    def list_accounts(
        self,
        db: Session,
        customer_id: int | None = None,
    ) -> list[Account]:
        return self.account_repo.get_all(db, customer_id)

    def get_account(
        self,
        db: Session,
        account_id: int,
    ) -> Account:
        account = self.account_repo.get_by_id(db, account_id)
        if account is None:
            raise AccountNotFoundError(
                f"Account with ID {account_id} not found."
            )
        return account

    def delete_account(
        self,
        db: Session,
        account_id: int,
    ) -> None:
        account = self.get_account(db, account_id)
        if self.account_repo.has_complaints(db, account_id):
            raise ResourceConflictError(
                "Account cannot be deleted while related complaints exist"
            )

        try:
            self.account_repo.delete(db, account)
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise ResourceConflictError(
                "The request conflicts with the current resource state"
            ) from exc
        except Exception:
            db.rollback()
            raise
