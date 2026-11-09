import re
import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import FastAPI, Request
from starlette.responses import Response

from app.database.base import Base
from app.api.routes import accounts, complaints, customers, health
from app.core.logging_config import configure_logging
from app.database.connection import engine
from app.schemas.root_schema import RootResponse
from app.error_handlers import (
    handle_unexpected_error,
    log_request,
    register_error_handlers,
)

Base.metadata.create_all(bind=engine)
configure_logging()
app = FastAPI()
register_error_handlers(app)




@app.middleware("http")
async def correlation_id_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    correlation_id = str(uuid4())
    request.state.correlation_id = correlation_id
    started_at = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception as exc:
        response = handle_unexpected_error(request, exc)
    response.headers["X-Correlation-ID"] = correlation_id
    status_code = response.status_code

    route_path = getattr(request.scope.get("route"), "path", "unmatched")
    log_request(
        correlation_id=correlation_id,
        operation=f"{request.method} {route_path}",
        outcome="success" if status_code < 400 else "error",
        duration_ms=(time.perf_counter() - started_at) * 1000,
        status_code=status_code,
    )
    return response


app.include_router(accounts.router)
app.include_router(complaints.router)
app.include_router(customers.router)
app.include_router(health.router)


@app.get("/", tags=["Root"], response_model=RootResponse)
def read_root():
    return {"message": "Welcome to the Banking Resolution Assistant API. Visit /docs for API documentation."}