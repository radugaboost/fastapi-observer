from typing import Any, Awaitable, Callable

from opentelemetry import trace
from opentelemetry.trace import format_trace_id
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from fastapi_observer.tracing.ctxvars import context_trace_id


class TracingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable[..., Awaitable[Any]]
    ) -> Response:
        span = trace.get_current_span()
        span_context = span.get_span_context()

        trace_id = format_trace_id(span_context.trace_id)
        context_trace_id.set(trace_id)

        return await call_next(request)
