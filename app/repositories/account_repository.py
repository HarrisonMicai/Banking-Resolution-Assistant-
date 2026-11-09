from sqlalchemy.orm import Session

from app.models import Account, Complaint


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

    def get_all(self, db: Session, customer_id: int | None = None) -> list[Account]:
        query = db.query(Account)
        if customer_id is not None:
            query = query.filter(Account.customer_id == customer_id)
        return query.order_by(Account.account_id).all()

    def delete(self, db: Session, account: Account) -> None:
        db.delete(account)

    def has_complaints(self, db: Session, account_id: int) -> bool:
        return (
            db.query(Complaint.complaint_id)
            .filter(Complaint.account_id == account_id)
            .first()
            is not None
        )
