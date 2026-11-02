from sqlalchemy.orm import Session
from app.models.complaint import Complaint, ComplaintStatus

class ComplaintRepository:
    def get_by_id(self, db: Session, complaint_id: int):
        return db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()

    def get_for_customer(self, db: Session, customer_id: int):
        return db.query(Complaint).filter(Complaint.customer_id == customer_id).all()

    def create(self, db: Session, complaint_data):
        complaint = Complaint(
            customer_id=complaint_data.customer_id,
            account_id=complaint_data.account_id,
            category=complaint_data.category,
            priority=complaint_data.priority,
            description=complaint_data.description,
            status=ComplaintStatus.SUBMITTED
        )
        db.add(complaint)
        db.commit()
        db.refresh(complaint)
        return complaint

    def update_status(self, db: Session, complaint: Complaint, new_status: ComplaintStatus, event_id: int, notes: str = None):
        # Utilizes domain model business logic method for status transition
        complaint.transition_status(new_status, event_id=event_id, notes=notes)
        db.commit()
        db.refresh(complaint)
        return complaint