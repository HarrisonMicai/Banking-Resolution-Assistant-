from dataclasses import dataclass, field
from datetime import datetime

from enum import Enum
# a set of symbolic names bound to unique, constant values (enumeration)
from typing import List, Optional

class ComplaintCategory(Enum):
    BILLING = "BILLING"
    FRAUD = "FRAUD"
    SERVICE = "SERVICE"
    ACCOUNT_MANAGEMENT = "ACCOUNT_MANAGEMENT"

class ComplaintPriority(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"

class ComplaintStatus(Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"

    @classmethod
    def valid_transitions(cls) -> dict:
        return {
            cls.SUBMITTED: [cls.UNDER_REVIEW, cls.REJECTED],
            cls.UNDER_REVIEW: [cls.RESOLVED, cls.CLOSED, cls.REJECTED],
            cls.RESOLVED: [cls.CLOSED],
            cls.CLOSED: [],
            cls.REJECTED: []
        }

@dataclass
class Customer:
    customer_id: str
    name: str
    email: str

@dataclass
class Account:
    account_id: str
    customer_id: str
    account_type: str
    balance: float

@dataclass
class ComplaintStatusEvent:
    event_id: str
    complaint_id: str
    previous_status: Optional[ComplaintStatus]
    new_status: ComplaintStatus
    timestamp: datetime = field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

@dataclass
class Complaint:
    complaint_id: str
    customer_id: str
    account_id: str
    category: ComplaintCategory
    priority: ComplaintPriority
    description: str
    status: ComplaintStatus = ComplaintStatus.SUBMITTED
    status_history: List[ComplaintStatusEvent] = field(default_factory=list)

    def transition_status(self, new_status: ComplaintStatus, event_id: str, notes: Optional[str] = None) -> None:
        allowed = ComplaintStatus.valid_transitions().get(self.status, [])
        if new_status not in allowed:
            raise ValueError(f"Invalid status transition from {self.status.name} to {new_status.name}")
        
        event = ComplaintStatusEvent(
            event_id=event_id,
            complaint_id=self.complaint_id,
            previous_status=self.status,
            new_status=new_status,
            notes=notes
        )
        self.status_history.append(event)
        self.status = new_status