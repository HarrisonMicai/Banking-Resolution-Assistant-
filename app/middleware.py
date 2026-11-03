import re
import time
from uuid import uuid4

from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.error_handlers import handle_unexpected_error, log_request

_CORRELATION_ID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-8][0-9a-fA-F]{3}-"
    r"[89aAbB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)


class CorrelationIdMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        supplied_id = headers.get(b"x-correlation-id", b"").decode(
            "ascii",
            errors="ignore",
        )
        correlation_id = (
            supplied_id
            if _CORRELATION_ID_PATTERN.fullmatch(supplied_id)
            else str(uuid4())
        )
        state = scope.setdefault("state", {})
        state["correlation_id"] = correlation_id
        started_at = time.perf_counter()
        status_code = 500
        response_started = False

        async def send_with_correlation_id(message: Message) -> None:
            nonlocal status_code, response_started
            if message["type"] == "http.response.start":
                status_code = message["status"]
                response_started = True
                response_headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() != b"x-correlation-id"
                ]
                response_headers.append(
                    (b"x-correlation-id", correlation_id.encode("ascii"))
                )
                message = {**message, "headers": response_headers}
            await send(message)

        try:
            await self.app(scope, receive, send_with_correlation_id)
        except Exception as exc:
            if response_started:
                raise
            request = Request(scope, receive)
            error_response: Response = await handle_unexpected_error(request, exc)
            await error_response(scope, receive, send_with_correlation_id)
            duration_ms = (time.perf_counter() - started_at) * 1000
            operation = _operation(scope)
            log_request(
                correlation_id=correlation_id,
                operation=operation,
                outcome="error",
                duration_ms=duration_ms,
                status_code=500,
            )
        else:
            duration_ms = (time.perf_counter() - started_at) * 1000
            operation = _operation(scope)
            log_request(
                correlation_id=correlation_id,
                operation=operation,
                outcome="success" if status_code < 400 else "error",
                duration_ms=duration_ms,
                status_code=status_code,
            )


def _operation(scope: Scope) -> str:
    route = scope.get("route")
    route_path = getattr(route, "path", "unmatched")
    return f"{scope['method']} {route_path}"
