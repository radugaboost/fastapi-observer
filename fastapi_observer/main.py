from fastapi import FastAPI

from fastapi_observer.config import ObserverConfig
from fastapi_observer.logging.middleware import LoggingMiddleware
from fastapi_observer.logging.setup import setup_logger
from fastapi_observer.metrics.middleware import MetricsMiddleware, metrics
from fastapi_observer.schemas import HealthCheck
from fastapi_observer.tracing.middleware import TracingMiddleware
from fastapi_observer.tracing.setup import setup_otel


def setup_observer(app: FastAPI, config: ObserverConfig) -> None:
    setup_logger()
    setup_otel(app, config.service_name)

    app.add_route("/metrics", metrics)

    app.add_middleware(TracingMiddleware)  # noqa
    app.add_middleware(MetricsMiddleware)  # noqa
    app.add_middleware(
        LoggingMiddleware,  # noqa
        sensitive_headers=config.sensitive_headers,
        sensitive_body_fields=config.sensitive_body_fields,
    )

    @app.get(
        "/health",
        tags=["healthcheck"],
        response_model=HealthCheck,
    )
    def get_health() -> HealthCheck:
        return HealthCheck()
