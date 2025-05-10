from json import JSONDecodeError, loads
from typing import Any, Awaitable, Callable

import structlog
from opentelemetry import trace
from opentelemetry.trace import NonRecordingSpan, format_span_id, format_trace_id
from starlette.datastructures import Headers
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable[..., Awaitable[Any]]
    ) -> Response:
        self.set_tracing_contextvars()
        self.process_headers(
            headers=request.headers,
            sensitive_headers=("authorization",),
        )

        raw_body = await request.body()
        self.process_body(raw_body)

        return await call_next(request)

    @staticmethod
    def set_tracing_contextvars() -> None:
        span = trace.get_current_span()
        if isinstance(span, NonRecordingSpan):
            return

        span_context = span.get_span_context()
        trace_id = format_trace_id(span_context.trace_id)
        span_id = format_span_id(span_context.span_id)

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            trace_id=trace_id,
            span_id=span_id,
        )

    @staticmethod
    def process_headers(
        headers: Headers,
        sensitive_headers: tuple[str, ...],
    ) -> None:
        filtered_headers = {}

        for key, value in headers.items():
            if key in sensitive_headers:
                filtered_headers[key] = "hidden"
                continue

            filtered_headers[key] = value

        logger.info("Processed request headers", headers=filtered_headers)

    @staticmethod
    def process_body(raw_body: bytes) -> None:
        try:
            body = loads(raw_body) if raw_body else {}
        except JSONDecodeError as err:
            logger.error("Failed to decode JSON", exc_info=err)
            body = {}

        logger.info("Processed request body", **body)
