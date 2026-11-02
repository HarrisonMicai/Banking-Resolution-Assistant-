from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models import (
    Account,
    Complaint,
    ComplaintCategory,
    ComplaintPriority,
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
    db.add(complaint)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Complaint could not be saved",
        )

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