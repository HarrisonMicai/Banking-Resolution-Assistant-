from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.service_errors import raise_http_exception
from app.database.connection import get_db
from app.schemas.customer_schema import CustomerCreate, CustomerRead, CustomerUpdate
from app.services.customer_service import CustomerService
from app.services.dependencies import get_customer_service
from app.services.exceptions import (
    CustomerNotFoundError,
    ServiceError,
)

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post(
    "",
    response_model=CustomerRead,
    status_code=status.HTTP_201_CREATED,
)
def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
    service: CustomerService = Depends(get_customer_service),
):
    try:
        return service.create_customer(
            db,
            name=customer_data.name,
            email=customer_data.email,
        )
    except ServiceError as exc:
        raise_http_exception(exc)


@router.get("", response_model=list[CustomerRead])
def list_customers(
    db: Session = Depends(get_db),
    service: CustomerService = Depends(get_customer_service),
):
    return service.list_customers(db)


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    service: CustomerService = Depends(get_customer_service),
):
    try:
        return service.get_customer(db, customer_id)
    except CustomerNotFoundError as exc:
        raise_http_exception(exc)


@router.patch("/{customer_id}", response_model=CustomerRead)
def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db),
    service: CustomerService = Depends(get_customer_service),
):
    updates = customer_data.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one customer field must be provided",
        )

    try:
        return service.update_customer(db, customer_id, updates)
    except ServiceError as exc:
        raise_http_exception(exc)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    service: CustomerService = Depends(get_customer_service),
):
    try:
        service.delete_customer(db, customer_id)
    except ServiceError as exc:
        raise_http_exception(exc)