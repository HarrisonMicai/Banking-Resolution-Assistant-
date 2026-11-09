from pydantic import BaseModel, ConfigDict


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
