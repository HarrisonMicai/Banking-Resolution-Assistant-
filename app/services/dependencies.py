from app.services.account_service import AccountService
from app.services.complaint_service import ComplaintService
from app.services.customer_service import CustomerService


def get_complaint_service() -> ComplaintService:
    return ComplaintService()


def get_account_service() -> AccountService:
    return AccountService()


def get_customer_service() -> CustomerService:
    return CustomerService()
