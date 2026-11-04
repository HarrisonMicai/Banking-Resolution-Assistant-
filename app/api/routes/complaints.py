from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.service_errors import raise_http_exception
from app.database.connection import get_db
from app.schemas.complaint_schema import (
    ComplaintCreate,
    ComplaintRead,
    ComplaintStatusUpdate,
)
from app.services.dependencies import get_complaint_service
from app.services.exceptions import ServiceError
from app.services.complaint_service import ComplaintService

router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.post(
    "",
    response_model=ComplaintRead,
    status_code=status.HTTP_201_CREATED,
)
def create_complaint(
    complaint_data: ComplaintCreate,
    db: Session = Depends(get_db),
    service: ComplaintService = Depends(get_complaint_service),
):
    try:
        return service.create_complaint(
            db,
            customer_id=complaint_data.customer_id,
            account_id=complaint_data.account_id,
            category=complaint_data.category,
            priority=complaint_data.priority,
            description=complaint_data.description,
        )
    except ServiceError as exc:
        raise_http_exception(exc)


@router.get("", response_model=list[ComplaintRead])
def list_complaints(
    customer_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    service: ComplaintService = Depends(get_complaint_service),
):
    return service.list_complaints(db, customer_id)


@router.get("/{complaint_id}", response_model=ComplaintRead)
def get_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    service: ComplaintService = Depends(get_complaint_service),
):
    try:
        return service.get_complaint(db, complaint_id)
    except ServiceError as exc:
        raise_http_exception(exc)


@router.patch("/{complaint_id}/status", response_model=ComplaintRead)
def update_complaint_status(
    complaint_id: int,
    status_update: ComplaintStatusUpdate,
    db: Session = Depends(get_db),
    service: ComplaintService = Depends(get_complaint_service),
):
    """Step 3: PATCH status with transition validation and history event notes."""
    try:
        return service.progress_complaint_status(
            db,
            complaint_id,
            status_update.new_status,
            event_id=status_update.event_id,
            notes=status_update.notes,
        )
    except ServiceError as exc:
        raise_http_exception(exc)