from pydantic import BaseModel, ConfigDict


class CustomerCreate(BaseModel):
    name: str
    email: str


class CustomerUpdate(BaseModel):
    name: str | None = None
    email: str | None = None


class CustomerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: int
    name: str
    email: str
