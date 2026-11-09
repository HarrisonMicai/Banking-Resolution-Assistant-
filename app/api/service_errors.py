from typing import NoReturn

from fastapi import HTTPException

from app.services.exceptions import ServiceError


def raise_http_exception(error: ServiceError) -> NoReturn:
    raise HTTPException(
        status_code=error.status_code,
        detail=error.http_detail,
    ) from error
