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
    def __init__(
        self,
        app: ASGIApp,
        *,
        sensitive_headers: tuple[str, ...] | None = None,
        sensitive_body_fields: tuple[str, ...] | None = None
    ) -> None:
        super().__init__(app)
        self.sensitive_headers = (
            tuple(h.lower() for h in sensitive_headers) if sensitive_headers else None
        )
        self.sensitive_body_fields = sensitive_body_fields

    async def dispatch(
        self, request: Request, call_next: Callable[..., Awaitable[Any]]
    ) -> Response:
        self.set_tracing_contextvars()
        logger.info(
            "Incoming HTTP request",
            path=request.url.path,
            method=request.method,
            query_params=dict(request.query_params),
        )

        self.process_headers(headers=request.headers)

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

    def process_headers(self, headers: Headers) -> None:
        headers_dict = dict(headers)

        if self.sensitive_headers:
            for sensitive_header in self.sensitive_headers:
                if sensitive_header in headers:
                    headers_dict[sensitive_header] = "hidden"

        logger.info("Processed request headers", headers=headers_dict)

    def process_body(self, raw_body: bytes) -> None:
        try:
            body = loads(raw_body) if raw_body else {}
        except (JSONDecodeError, UnicodeDecodeError):
            logger.error("Failed to decode JSON", exc_info=True)
            body = {}

        if self.sensitive_body_fields:
            for sensitive_field in self.sensitive_body_fields:
                if sensitive_field in body:
                    body[sensitive_field] = "hidden"

        logger.info("Processed request body", body=body)
