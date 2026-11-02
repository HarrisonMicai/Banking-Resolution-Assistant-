# Service: business behavior and transaction use cases.
from sqlalchemy.orm import Session
from app.repositories.complaint_repository import ComplaintRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.account_repository import AccountRepository
from app.models.models import ComplaintStatus

class ComplaintService:
    def __init__(
        self, 
        complaint_repo: ComplaintRepository = None, 
        customer_repo: CustomerRepository = None, 
        account_repo: AccountRepository = None
    ):
        # Dependency injection allows passing mock/fake repositories for testing
        self.complaint_repo = complaint_repo or ComplaintRepository()
        self.customer_repo = customer_repo or CustomerRepository()
        self.account_repo = account_repo or AccountRepository()

    def create_complaint(self, db: Session, complaint_data):
        # Validate that customer and account exist before creation
        customer = self.customer_repo.get_by_id(db, complaint_data.customer_id)
        if not customer:
            raise ValueError(f"Customer with ID {complaint_data.customer_id} not found.")
        account = self.account_repo.get_by_id(db, complaint_data.account_id)
        if not account:
            raise ValueError(f"Account with ID {complaint_data.account_id} not found.")

    def get_complaint(self, db: Session, complaint_id: int):
        complaint = self.complaint_repo.get_by_id(db, complaint_id)
        if not complaint:
            raise ValueError(f"Complaint with ID {complaint_id} not found.")
        return complaint

    def progress_complaint_status(self, 
                                  db: Session, 
                                  complaint_id: int, 
                                  new_status: ComplaintStatus, 
                                  event_id: int, 
                                  notes: str = None
                                  ):
        complaint = self.get_complaint(db, complaint_id)
        
        # Delegates status transition rule enforcement to domain model via repo
        return self.complaint_repo.update_status(db, complaint, new_status, event_id, notes)