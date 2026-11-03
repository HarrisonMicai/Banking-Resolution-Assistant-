from pydantic import BaseModel, Field
class ComplaintCreate(BaseModel):
    customer_id:str = Field(..., description="ID of the customer who filed the complaint")
    account_id:str = Field(..., description="ID of the account related to the complaint")
    category:str = Field(..., description="Category of the complaint")
    priority:str = Field(..., description="Priority level of the complaint")
    description:str = Field(..., description="Description of the complaint")

class ComplaintResponse(BaseModel):
    id:int = Field(..., description="ID of the complaint")
    customer_id:str = Field(..., description="ID of the customer who filed the complaint")
    account_id:str = Field(..., description="ID of the account related to the complaint")
    category:str = Field(..., description="Category of the complaint")
    priority:str = Field(..., description="Priority level of the complaint")
    description:str = Field(..., description="Description of the complaint")
    status:str = Field(..., description="Current status of the complaint")
    date_opened:str = Field(..., description="Date the complaint was opened")
    date_closed:str = Field(..., description="Date the complaint was closed")


class ComplaintUpdate(BaseModel):
    category:str = Field(..., description="Category of the complaint")
    priority:str = Field(..., description="Priority level of the complaint")
    description:str = Field(..., description="Description of the complaint")
    status:str = Field(..., description="Current status of the complaint")