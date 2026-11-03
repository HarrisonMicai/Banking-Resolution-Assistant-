import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("banking_api")


class ErrorResponse(BaseModel):
    code: str
    message: str
    correlation_id: str


ERROR_CATALOG: dict[str, tuple[int, str]] = {
    "CUSTOMER_NOT_FOUND": (404, "Customer not found"),
    "COMPLAINT_NOT_FOUND": (404, "Complaint not found"),
    "ACCOUNT_NOT_FOUND": (404, "Account not found for this customer"),
    "INVALID_STATUS_TRANSITION": (409, "Invalid complaint status transition"),
    "CONFLICT": (409, "The request conflicts with the current resource state"),
    "VALIDATION_ERROR": (422, "Request validation failed"),
    "RESOURCE_NOT_FOUND": (404, "Requested resource was not found"),
    "BAD_REQUEST": (400, "The request could not be completed"),
    "DEPENDENCY_UNAVAILABLE": (503, "A required service is unavailable"),
    "INTERNAL_ERROR": (500, "An unexpected error occurred"),
}

HTTP_ERROR_CODES = {
    "Customer not found": "CUSTOMER_NOT_FOUND",
    "Complaint not found": "COMPLAINT_NOT_FOUND",
    "Account not found for this customer": "ACCOUNT_NOT_FOUND",
    "Invalid complaint status transition": "INVALID_STATUS_TRANSITION",
    "Invalid status transition": "INVALID_STATUS_TRANSITION",
    "A customer with this email already exists": "CONFLICT",
    "The request conflicts with the current resource state": "CONFLICT",
    "Complaint and initial status event could not be saved": "CONFLICT",
    "At least one customer field must be provided": "VALIDATION_ERROR",
    "Customer cannot be deleted while related records exist": "CONFLICT",
    "A required service is unavailable": "DEPENDENCY_UNAVAILABLE",
}


def _correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", "unknown")


def _error_response(
    request: Request,
    code: str,
    message: str,
    status_code: int,
) -> JSONResponse:
    correlation_id = _correlation_id(request)
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            code=code,
            message=message,
            correlation_id=correlation_id,
        ).model_dump(),
        headers={"X-Correlation-ID": correlation_id},
    )


async def handle_validation_error(
    request: Request,
    _exc: RequestValidationError,
) -> JSONResponse:
    del _exc
    _, message = ERROR_CATALOG["VALIDATION_ERROR"]
    code = "VALIDATION_ERROR"
    return _error_response(request, code, message, 422)


async def handle_http_error(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else ""
    code = HTTP_ERROR_CODES.get(detail)
    if code is None:
        code = {
            422: "VALIDATION_ERROR",
            409: "CONFLICT",
            404: "RESOURCE_NOT_FOUND",
            400: "BAD_REQUEST",
            503: "DEPENDENCY_UNAVAILABLE",
        }.get(exc.status_code, "INTERNAL_ERROR")
    _, safe_message = ERROR_CATALOG[code]
    return _error_response(request, code, safe_message, exc.status_code)


async def handle_database_error(
    request: Request,
    _exc: SQLAlchemyError,
) -> JSONResponse:
    del _exc
    code = "DEPENDENCY_UNAVAILABLE"
    _, message = ERROR_CATALOG[code]
    return _error_response(request, code, message, 503)


async def handle_unexpected_error(
    request: Request,
    _exc: Exception,
) -> JSONResponse:
    del _exc
    code = "INTERNAL_ERROR"
    _, message = ERROR_CATALOG[code]
    return _error_response(request, code, message, 500)


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(StarletteHTTPException, handle_http_error)
    app.add_exception_handler(SQLAlchemyError, handle_database_error)
    app.add_exception_handler(Exception, handle_unexpected_error)


def log_request(
    *,
    correlation_id: str,
    operation: str,
    outcome: str,
    duration_ms: float,
    status_code: int,
) -> None:
    level = logging.ERROR if status_code >= 500 else (
        logging.WARNING if status_code >= 400 else logging.INFO
    )
    logger.log(
        level,
        "request_complete",
        extra={
            "correlation_id": correlation_id,
            "operation": operation,
            "outcome": outcome,
            "duration_ms": round(duration_ms, 2),
            "status_code": status_code,
        },
    )
