from sqlalchemy.orm import Session

from app.models import Account, Complaint, Customer


class CustomerRepository:
    def create(self, db: Session, *, name: str, email: str) -> Customer:
        customer = Customer(name=name, email=email)
        db.add(customer)
        return customer

    def get_by_id(self, db: Session, customer_id: int) -> Customer | None:
        return db.get(Customer, customer_id)

    def get_all(self, db: Session) -> list[Customer]:
        return db.query(Customer).order_by(Customer.customer_id).all()

    def update(
        self,
        db: Session,
        customer: Customer,
        updates: dict[str, str | None],
    ) -> None:
        db.add(customer)
        for field, value in updates.items():
            setattr(customer, field, value)

    def delete(self, db: Session, customer: Customer) -> None:
        db.delete(customer)

    def has_related_records(self, db: Session, customer_id: int) -> bool:
        has_accounts = (
            db.query(Account.account_id)
            .filter(Account.customer_id == customer_id)
            .first()
            is not None
        )
        has_complaints = (
            db.query(Complaint.complaint_id)
            .filter(Complaint.customer_id == customer_id)
            .first()
            is not None
        )
        return has_accounts or has_complaints
