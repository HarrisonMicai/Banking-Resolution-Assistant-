from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models import Account, Customer

router = APIRouter(prefix="/accounts", tags=["Accounts"])


class AccountCreate(BaseModel):
    customer_id: int
    account_type: str
    balance: float = 0.0


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: int
    customer_id: int
    account_type: str
    balance: float


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    account_data: AccountCreate,
    db: Session = Depends(get_db),
):
    if db.get(Customer, account_data.customer_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    account = Account(**account_data.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account
