
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Enum as SQLAlchemyEnum,
    Text
)
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from typing import Optional

from app.database.base import Base


# -------------------------
# ENUMS
# -------------------------

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
    def valid_transitions(cls):
        return {
            cls.SUBMITTED: [cls.UNDER_REVIEW, cls.REJECTED],
            cls.UNDER_REVIEW: [
                cls.RESOLVED,
                cls.CLOSED,
                cls.REJECTED
            ],
            cls.RESOLVED: [cls.CLOSED],
            cls.CLOSED: [],
            cls.REJECTED: []
        }


# -------------------------
# CUSTOMER TABLE
# -------------------------

class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)

    # Relationships
    accounts = relationship("Account", back_populates="customer")
    complaints = relationship("Complaint", back_populates="customer")

 

# -------------------------
# ACCOUNT TABLE
# -------------------------

class Account(Base):
    __tablename__ = "accounts"

    account_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    account_type = Column(String, nullable=False)
    balance = Column(Float, nullable=False, default=0.0)

    # Relationships
    customer = relationship("Customer", back_populates="accounts")
    complaints = relationship("Complaint", back_populates="account")


# -------------------------
# COMPLAINT TABLE
# -------------------------

class Complaint(Base):
    __tablename__ = "complaints"

    complaint_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.account_id"), nullable=False)

    category = Column(
        SQLAlchemyEnum(ComplaintCategory),
        nullable=False
    )

    priority = Column(
        SQLAlchemyEnum(ComplaintPriority),
        nullable=False
    )

    description = Column(Text, nullable=False)

    status = Column(
        SQLAlchemyEnum(ComplaintStatus),
        nullable=False,
        default=ComplaintStatus.SUBMITTED
    )

    # Relationships
    customer = relationship("Customer", back_populates="complaints")
    account = relationship("Account", back_populates="complaints")

    status_history = relationship(
        "ComplaintStatusEvent",
        back_populates="complaint",
        cascade="all, delete-orphan",
        order_by="ComplaintStatusEvent.timestamp"
    )

    # Business logic for status transitions
    def transition_status(
        self,
        new_status: ComplaintStatus,
        event_id: int,
        notes: Optional[str] = None
    ):

        allowed = ComplaintStatus.valid_transitions().get(
            self.status, []
        )

        if new_status not in allowed:
            raise ValueError(
                f"Invalid status transition from "
                f"{self.status.name} to {new_status.name}"
            )

        event = ComplaintStatusEvent(
            event_id=event_id,
            previous_status=self.status,
            new_status=new_status,
            notes=notes
        )

        self.status_history.append(event)
        self.status = new_status


# -------------------------
# COMPLAINT STATUS EVENT TABLE
# -------------------------

class ComplaintStatusEvent(Base):
    __tablename__ = "complaint_status_events"

    event_id = Column(Integer, primary_key=True, index=True)

    complaint_id = Column(
        Integer,
        ForeignKey("complaints.complaint_id"),
        nullable=False
    )

    previous_status = Column(
        SQLAlchemyEnum(ComplaintStatus),
        nullable=True
    )

    new_status = Column(
        SQLAlchemyEnum(ComplaintStatus),
        nullable=False
    )

    timestamp = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    notes = Column(Text, nullable=True)

    # Relationship
    complaint = relationship(
        "Complaint",
        back_populates="status_history"
    )
