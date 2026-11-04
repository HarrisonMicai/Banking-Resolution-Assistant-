from pydantic import BaseModel, ConfigDict

from app.models import ComplaintCategory, ComplaintPriority, ComplaintStatus


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
