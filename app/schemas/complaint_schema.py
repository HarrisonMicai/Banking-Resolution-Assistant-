from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict
from pydantic.types import StringConstraints

from app.models import (
    ComplaintCategory,
    ComplaintPriority,
    ComplaintStatus,
)


class ComplaintCreate(BaseModel):
    customer_id: int
    account_id: int
    category: ComplaintCategory
    priority: ComplaintPriority
    description: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ComplaintRead(ComplaintCreate):
    model_config = ConfigDict(from_attributes=True)

    complaint_id: int
    status: str


class ComplaintStatusUpdate(BaseModel):
    new_status: ComplaintStatus
    event_id: int
    notes: str | None = None


class ComplaintStatusEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: int
    previous_status: ComplaintStatus | None = None
    new_status: ComplaintStatus
    timestamp: datetime
    notes: str | None = None
