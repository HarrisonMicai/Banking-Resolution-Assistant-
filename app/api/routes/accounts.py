from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.service_errors import raise_http_exception
from app.database.connection import get_db
from app.schemas.account_schema import AccountCreate, AccountRead
from app.services.account_service import AccountService
from app.services.dependencies import get_account_service
from app.services.exceptions import ServiceError

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    account_data: AccountCreate,
    db: Session = Depends(get_db),
    service: AccountService = Depends(get_account_service),
):
    try:
        return service.create_account(
            db,
            customer_id=account_data.customer_id,
            account_type=account_data.account_type,
            balance=account_data.balance,
        )
    except ServiceError as exc:
        raise_http_exception(exc)
