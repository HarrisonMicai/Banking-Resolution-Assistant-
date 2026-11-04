from sqlalchemy.orm import Session

from app.models import Account


class AccountRepository:
    def create(
        self,
        db: Session,
        *,
        customer_id: int,
        account_type: str,
        balance: float,
    ) -> Account:
        account = Account(
            customer_id=customer_id,
            account_type=account_type,
            balance=balance,
        )
        db.add(account)
        return account

    def get_by_id(self, db: Session, account_id: int) -> Account | None:
        return db.get(Account, account_id)

    def get_all(self, db: Session) -> list[Account]:
        return db.query(Account).order_by(Account.account_id).all()
