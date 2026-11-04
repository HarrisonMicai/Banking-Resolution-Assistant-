from sqlalchemy.orm import Session

from app.models import (
    Complaint,
    ComplaintCategory,
    ComplaintPriority,
    ComplaintStatus,
    ComplaintStatusEvent,
)


class ComplaintRepository:
    def get_by_id(self, db: Session, complaint_id: int) -> Complaint | None:
        return db.get(Complaint, complaint_id)

    def get_all(
        self,
        db: Session,
        customer_id: int | None = None,
    ) -> list[Complaint]:
        query = db.query(Complaint)
        if customer_id is not None:
            query = query.filter(Complaint.customer_id == customer_id)
        return query.order_by(Complaint.complaint_id).all()

    def create(
        self,
        db: Session,
        *,
        customer_id: int,
        account_id: int,
        category: ComplaintCategory,
        priority: ComplaintPriority,
        description: str,
    ) -> Complaint:
        complaint = Complaint(
            customer_id=customer_id,
            account_id=account_id,
            category=category,
            priority=priority,
            description=description,
            status=ComplaintStatus.SUBMITTED,
        )
        db.add(complaint)
        db.flush()
        db.add(
            ComplaintStatusEvent(
                complaint_id=complaint.complaint_id,
                previous_status=None,
                new_status=ComplaintStatus.SUBMITTED,
            )
        )
        return complaint

    def update_status(
        self,
        db: Session,
        complaint: Complaint,
        new_status: ComplaintStatus,
        event_id: int,
        notes: str | None = None,
    ) -> Complaint:
        del db
        complaint.transition_status(
            new_status,
            event_id=event_id,
            notes=notes,
        )
        return complaint
