from fastapi import FastAPI

from fastapi_observer.logging.middleware import LoggingMiddleware
from fastapi_observer.logging.setup import setup_logger
from fastapi_observer.metrics.middleware import MetricsMiddleware, metrics
from fastapi_observer.schemas import HealthCheck
from fastapi_observer.tracing.middleware import TracingMiddleware
from fastapi_observer.tracing.setup import setup_otel


def setup_middlewares(app: FastAPI) -> None:
    app.add_middleware(MetricsMiddleware)  # noqa
    app.add_middleware(TracingMiddleware)  # noqa
    app.add_middleware(LoggingMiddleware)  # noqa


def setup_observer(app: FastAPI, service_name: str) -> None:
    setup_logger()
    setup_middlewares(app)
    setup_otel(app, service_name)

    app.add_route("/metrics", metrics)

    @app.get(
        "/health",
        tags=["healthcheck"],
        response_model=HealthCheck,
    )
    def get_health() -> HealthCheck:
        return HealthCheck()
