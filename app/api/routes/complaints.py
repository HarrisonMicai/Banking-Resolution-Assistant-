from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models import (
    Account,
    Complaint,
    ComplaintCategory,
    ComplaintPriority,
    ComplaintStatus,
    ComplaintStatusEvent,
    Customer,
)

router = APIRouter(prefix="/complaints", tags=["Complaints"])


class ComplaintCreate(BaseModel):
    customer_id: int
    account_id: int
    category: ComplaintCategory
    priority: ComplaintPriority
    description: str


class ComplaintRead(ComplaintCreate):
    model_config = ConfigDict(from_attributes=True)

    complaint_id: int
    status: str


class ComplaintStatusUpdate(BaseModel):
    new_status: ComplaintStatus
    event_id: int
    notes: str | None = None


@router.post(
    "",
    response_model=ComplaintRead,
    status_code=status.HTTP_201_CREATED,
)
def create_complaint(
    complaint_data: ComplaintCreate,
    db: Session = Depends(get_db),
):
    customer = db.get(Customer, complaint_data.customer_id)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    account = db.get(Account, complaint_data.account_id)
    if account is None or account.customer_id != complaint_data.customer_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found for this customer",
        )

    complaint = Complaint(**complaint_data.model_dump())
    try:
        # Stage the complaint first. flush() sends the INSERT to the database
        # and populates its generated complaint_id, but does not commit it.
        db.add(complaint)
        db.flush()

        # The initial status event is part of complaint creation, not a
        # separate operation. Link it to the generated complaint ID and
        # record the starting SUBMITTED status in the history.
        db.add(
            ComplaintStatusEvent(
                complaint_id=complaint.complaint_id,
                previous_status=None,
                new_status=ComplaintStatus.SUBMITTED,
            )
        )

        # This is the single commit point: both inserts become durable
        # together, or neither does.
        db.commit()
    except IntegrityError:
        # A constraint failure in either insert invalidates the whole unit
        # of work, including a complaint that was already flushed.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Complaint and initial status event could not be saved",
        )
    except SQLAlchemyError:
        # Roll back any database-level failure so no partial create remains.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Complaint and initial status event could not be saved",
        )
    except Exception:
        # Preserve unexpected errors while still leaving the session clean.
        db.rollback()
        raise

    # Reload committed values (including database-generated fields) before
    # returning the complaint through the response schema.
    db.refresh(complaint)
    return complaint


@router.get("", response_model=list[ComplaintRead])
def list_complaints(
    customer_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Complaint)
    if customer_id is not None:
        query = query.filter(Complaint.customer_id == customer_id)
    return query.order_by(Complaint.complaint_id).all()


@router.get("/{complaint_id}", response_model=ComplaintRead)
def get_complaint(complaint_id: int, db: Session = Depends(get_db)):
    complaint = db.get(Complaint, complaint_id)
    if complaint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found",
        )
    return complaint


@router.patch("/{complaint_id}/status", response_model=ComplaintRead)
def update_complaint_status(
    complaint_id: int,
    status_update: ComplaintStatusUpdate,
    db: Session = Depends(get_db),
):
    """Step 3: PATCH status with transition validation and history event notes."""
    complaint = db.get(Complaint, complaint_id)
    if complaint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found",
        )

    try:
        complaint.transition_status(
            status_update.new_status,
            event_id=status_update.event_id,
            notes=status_update.notes,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invalid complaint status transition",
        ) from exc

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The request conflicts with the current resource state",
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="A required service is unavailable",
        )

    db.refresh(complaint)
    return complaint