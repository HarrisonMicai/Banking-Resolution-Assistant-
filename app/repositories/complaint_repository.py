from sqlalchemy.orm import Session

from app.models import (
    Complaint,
    ComplaintCategory,
    ComplaintPriority,
    ComplaintSoftDeletion,
    ComplaintStatus,
    ComplaintStatusEvent,
)


class ComplaintRepository:
    def get_by_id(self, db: Session, complaint_id: int) -> Complaint | None:
        return (
            db.query(Complaint)
            .outerjoin(
                ComplaintSoftDeletion,
                ComplaintSoftDeletion.complaint_id == Complaint.complaint_id,
            )
            .filter(
                Complaint.complaint_id == complaint_id,
                ComplaintSoftDeletion.complaint_id.is_(None),
            )
            .first()
        )

    def get_all(
        self,
        db: Session,
        customer_id: int | None = None,
        account_id: int | None = None,
    ) -> list[Complaint]:
        query = (
            db.query(Complaint)
            .outerjoin(
                ComplaintSoftDeletion,
                ComplaintSoftDeletion.complaint_id == Complaint.complaint_id,
            )
            .filter(ComplaintSoftDeletion.complaint_id.is_(None))
        )
        if customer_id is not None:
            query = query.filter(Complaint.customer_id == customer_id)
        if account_id is not None:
            query = query.filter(Complaint.account_id == account_id)
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

    def get_status_history(
        self,
        db: Session,
        complaint_id: int,
    ) -> list[ComplaintStatusEvent]:
        return (
            db.query(ComplaintStatusEvent)
            .filter(ComplaintStatusEvent.complaint_id == complaint_id)
            .order_by(
                ComplaintStatusEvent.timestamp,
                ComplaintStatusEvent.event_id,
            )
            .all()
        )

    def soft_delete(
        self,
        db: Session,
        complaint: Complaint,
        deleted_by: str,
    ) -> None:
        db.add(
            ComplaintSoftDeletion(
                complaint_id=complaint.complaint_id,
                deleted_by=deleted_by,
            )
        )
