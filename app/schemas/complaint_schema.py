from pydantic import BaseModel
class ComplaintCreate(BaseModel):
    customer_id:str
    account_id:str
    category:str
    priority:str
    description:str

class ComplaintResponse(BaseModel):
    id:int
    customer_id:str
    account_id:str
    category:str
    priority:str
    description:str
    status:str
    date_opened:str
    date_closed:str