import os
from time import monotonic
from typing import Any, Awaitable, Callable, Dict, List

import prometheus_client
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, CollectorRegistry, generate_latest
from prometheus_client.multiprocess import MultiProcessCollector
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

DEFAULT_BUCKETS = (
    0.005,
    0.01,
    0.025,
    0.05,
    0.075,
    0.1,
    0.125,
    0.15,
    0.175,
    0.2,
    0.25,
    0.3,
    0.5,
    0.75,
    1.0,
    2.5,
    5.0,
    7.5,
    float("+inf"),
)

REQUEST_COUNT = prometheus_client.Counter(
    "http_requests_total",
    "Total count of HTTP requests",
    ["method", "endpoint", "http_status"],
)

ERROR_COUNT = prometheus_client.Counter(
    "http_errors_total",
    "Total count of HTTP errors",
    ["method", "endpoint", "http_status"],
)

INTEGRATIONS_LATENCY = prometheus_client.Histogram(
    "integrations_latency_seconds",
    "",
    ["integration"],
    buckets=DEFAULT_BUCKETS,
)

ROUTES_LATENCY = prometheus_client.Histogram(
    "routes_latency_seconds",
    "",
    ["method", "endpoint"],
    buckets=DEFAULT_BUCKETS,
)


def async_integrations_timer(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    async def wrapper(*args: List[Any], **kwargs: Dict[Any, Any]) -> Awaitable[Any]:
        start_time: float = monotonic()
        result = await func(*args, **kwargs)
        INTEGRATIONS_LATENCY.labels(integration=func.__name__).observe(monotonic() - start_time)
        return result

    return wrapper


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = monotonic()
        response = await call_next(request)
        process_time = monotonic() - start_time
        method = request.method
        endpoint = request.url.path
        status_code = response.status_code

        REQUEST_COUNT.labels(method=method, endpoint=endpoint, http_status=status_code).inc()
        if status_code >= 400:
            ERROR_COUNT.labels(method=method, endpoint=endpoint, http_status=status_code).inc()

        ROUTES_LATENCY.labels(method=method, endpoint=endpoint).observe(process_time)

        return response


def metrics(_: Request) -> Response:
    if "prometheus_multiproc_dir" in os.environ:
        registry = CollectorRegistry()
        MultiProcessCollector(registry)
    else:
        registry = REGISTRY

    return Response(generate_latest(registry), headers={"Content-Type": CONTENT_TYPE_LATEST})
