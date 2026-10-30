
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from sqlalchemy import (
    String,
    Integer,
    DateTime,
    ForeignKey,
    Enum as SQLAlchemyEnum,
    Numeric,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
# CUSTOMER MODEL
# -------------------------

class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[str] = mapped_column(
        String(36), primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )

    accounts: Mapped[List["Account"]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan"
    )

    complaints: Mapped[List["Complaint"]] = relationship(
        back_populates="customer"
    )


# -------------------------
# ACCOUNT MODEL
# -------------------------

class Account(Base):
    __tablename__ = "accounts"

    account_id: Mapped[str] = mapped_column(
        String(36), primary_key=True
    )

    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.customer_id"),
        nullable=False
    )

    account_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )

    balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )

    customer: Mapped["Customer"] = relationship(
        back_populates="accounts"
    )

    complaints: Mapped[List["Complaint"]] = relationship(
        back_populates="account"
    )


# -------------------------
# COMPLAINT MODEL
# -------------------------

class Complaint(Base):
    __tablename__ = "complaints"

    complaint_id: Mapped[str] = mapped_column(
        String(36), primary_key=True
    )

    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.customer_id"),
        nullable=False
    )

    account_id: Mapped[str] = mapped_column(
        ForeignKey("accounts.account_id"),
        nullable=False
    )

    category: Mapped[ComplaintCategory] = mapped_column(
        SQLAlchemyEnum(
            ComplaintCategory,
            name="complaint_category",
            native_enum=False
        ),
        nullable=False
    )

    priority: Mapped[ComplaintPriority] = mapped_column(
        SQLAlchemyEnum(
            ComplaintPriority,
            name="complaint_priority",
            native_enum=False
        ),
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    status: Mapped[ComplaintStatus] = mapped_column(
        SQLAlchemyEnum(
            ComplaintStatus,
            name="complaint_status",
            native_enum=False
        ),
        nullable=False,
        default=ComplaintStatus.SUBMITTED
    )

    customer: Mapped["Customer"] = relationship(
        back_populates="complaints"
    )

    account: Mapped["Account"] = relationship(
        back_populates="complaints"
    )

    status_history: Mapped[List["ComplaintStatusEvent"]] = relationship(
        back_populates="complaint",
        cascade="all, delete-orphan",
        order_by="ComplaintStatusEvent.timestamp"
    )

    def transition_status(
        self,
        new_status: ComplaintStatus,
        event_id: str,
        notes: Optional[str] = None
    ) -> None:

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
# COMPLAINT STATUS EVENT MODEL
# -------------------------

class ComplaintStatusEvent(Base):
    __tablename__ = "complaint_status_events"

    event_id: Mapped[str] = mapped_column(
        String(36), primary_key=True
    )

    complaint_id: Mapped[str] = mapped_column(
        ForeignKey("complaints.complaint_id"),
        nullable=False
    )

    previous_status: Mapped[Optional[ComplaintStatus]] = mapped_column(
        SQLAlchemyEnum(
            ComplaintStatus,
            name="previous_complaint_status",
            native_enum=False
        ),
        nullable=True
    )

    new_status: Mapped[ComplaintStatus] = mapped_column(
        SQLAlchemyEnum(
            ComplaintStatus,
            name="new_complaint_status",
            native_enum=False
        ),
        nullable=False
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

    complaint: Mapped["Complaint"] = relationship(
        back_populates="status_history"
    )
