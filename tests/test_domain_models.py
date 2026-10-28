from datetime import datetime
import pytest
from models import (
    Account,
    Complaint,
    ComplaintCategory,
    ComplaintPriority,
    ComplaintStatus,
    Customer,
)

def test_valid_complaint_creation():
    customer = Customer(customer_id="C123", name="Jane Doe", email="jane@example.com")
    account = Account(account_id="A999", customer_id="C123", account_type="CHECKING", balance=1500.0)
    complaint = Complaint(
        complaint_id="CMP-01",
        customer_id=customer.customer_id,
        account_id=account.account_id,
        category=ComplaintCategory.BILLING,
        priority=ComplaintPriority.HIGH,
        description="Incorrect overdraft fee applied."
    )
    
    assert complaint.status == ComplaintStatus.SUBMITTED
    assert complaint.category == ComplaintCategory.BILLING

def test_valid_status_transition():
    complaint = Complaint(
        complaint_id="CMP-02",
        customer_id="C123",
        account_id="A999",
        category=ComplaintCategory.FRAUD,
        priority=ComplaintPriority.URGENT,
        description="Unauthorized transaction."
    )
    
    complaint.transition_status(ComplaintStatus.UNDER_REVIEW, event_id="EVT-1", notes="Assigned to investigator.")
    assert complaint.status == ComplaintStatus.UNDER_REVIEW
    assert len(complaint.status_history) == 1

def test_invalid_status_transition_raises_error():
    complaint = Complaint(
        complaint_id="CMP-03",
        customer_id="C123",
        account_id="A999",
        category=ComplaintCategory.SERVICE,
        priority=ComplaintPriority.LOW,
        description="Poor customer service."
    )
    
    # Attempting an illegal jump from SUBMITTED directly to RESOLVED
    with pytest.raises(ValueError, match="Invalid status transition"):
        complaint.transition_status(ComplaintStatus.RESOLVED, event_id="EVT-2")