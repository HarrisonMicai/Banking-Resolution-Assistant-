class ServiceError(Exception):
    status_code = 500
    http_detail = "An unexpected error occurred"


class CustomerNotFoundError(ServiceError):
    status_code = 404
    http_detail = "Customer not found"


class AccountNotFoundError(ServiceError):
    status_code = 404
    http_detail = "Account not found for this customer"


class ComplaintNotFoundError(ServiceError):
    status_code = 404
    http_detail = "Complaint not found"


class InvalidComplaintTransitionError(ServiceError):
    status_code = 409
    http_detail = "Invalid complaint status transition"


class ResourceConflictError(ServiceError):
    status_code = 409
    http_detail = "The request conflicts with the current resource state"

    def __init__(self, detail: str):
        super().__init__(detail)
        self.http_detail = detail


class ComplaintCreationError(ServiceError):
    status_code = 500
    http_detail = "Complaint and initial status event could not be saved"


class DependencyUnavailableError(ServiceError):
    status_code = 503
    http_detail = "A required service is unavailable"
