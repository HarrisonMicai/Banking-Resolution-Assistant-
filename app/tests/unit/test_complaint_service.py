import pytest
from unittest.mock import MagicMock
from app.services.ComplaintService import ComplaintService
from app.models.models import Complaint, ComplaintStatus, ComplaintCategory, ComplaintPriority

# --- STEP 2: FIXTURES ---

class FakeCustomerRepo:
    def __init__(self, exists=True):
        self.exists = exists
    def get_by_id(self, db, customer_id):
        if self.exists:
            return MagicMock(customer_id=customer_id)
        return None

class FakeAccountRepo:
    def __init__(self, exists=True):
        self.exists = exists
    def get_by_id(self, db, account_id):
        if self.exists:
            return MagicMock(account_id=account_id)
        return None

class FakeComplaintRepo:
    def __init__(self, complaint_obj=None):
        self.complaint_obj = complaint_obj
    def get_by_id(self, db, complaint_id):
        return self.complaint_obj
    def update_status(self, db, complaint, new_status, event_id, notes):
        complaint.transition_status(new_status, event_id, notes)
        return complaint


@pytest.fixture
def mock_db():
    return MagicMock()


# --- STEP 3: TESTS WITH PARAMETRIZATION ---

@pytest.mark.parametrize(
    "initial_status,target_status,should_succeed",
    [
        (ComplaintStatus.SUBMITTED, ComplaintStatus.UNDER_REVIEW, True),
        (ComplaintStatus.SUBMITTED, ComplaintStatus.CLOSED, False), # Invalid transition rule
        (ComplaintStatus.UNDER_REVIEW, ComplaintStatus.RESOLVED, True),
        (ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED, True),
        (ComplaintStatus.CLOSED, ComplaintStatus.SUBMITTED, False),
    ]
)
def test_status_transition_rules(initial_status, target_status, should_succeed):
    complaint = Complaint(
        complaint_id=1,
        customer_id=101,
        account_id=202,
        category=ComplaintCategory.BILLING,
        priority=ComplaintPriority.MEDIUM,
        description="Billing error encountered on monthly statement.",
        status=initial_status
    )
    
    if should_succeed:
        complaint.transition_status(target_status, event_id=1, notes="Transition test")
        assert complaint.status == target_status
        assert len(complaint.status_history) == 1
    else:
        with pytest.raises(ValueError):
            complaint.transition_status(target_status, event_id=1, notes="Invalid transition test")


def test_create_complaint_missing_customer(mock_db):
    service = ComplaintService(
        customer_repo=FakeCustomerRepo(exists=False),
        account_repo=FakeAccountRepo(exists=True)
    )
    complaint_data = MagicMock(customer_id=999, account_id=100)
    
    with pytest.raises(ValueError, match="Customer with ID 999 not found"):
        service.create_complaint(mock_db, complaint_data)