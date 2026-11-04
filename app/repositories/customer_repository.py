from sqlalchemy.orm import Session

from app.models import Customer


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
