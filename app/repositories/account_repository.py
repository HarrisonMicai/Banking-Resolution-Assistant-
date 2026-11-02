from sqlalchemy.orm import Session
from app.models.models import Account

class AccountRepository:
    def create(self, db: Session, account_data):
        account = Account(
            customer_id=account_data.customer_id,
            account_type=account_data.account_type,
            balance=account_data.balance
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        return account

    def get_by_id(self, db: Session, account_id: int):
        return db.query(Account).filter(Account.account_id == account_id).first()

    def get_all(self, db: Session):
        return db.query(Account).all()