import logging
from typing import Any

import structlog


def setup_logger(enable_json: bool = True) -> None:
    processors: list[Any] = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(),
        structlog.processors.StackInfoRenderer(),
    ]

    structlog.configure(
        processors=processors + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    render = (
        structlog.processors.JSONRenderer(ensure_ascii=False)
        if enable_json
        else structlog.dev.ConsoleRenderer(colors=True)
    )

    _configure_default_logging_by_custom(processors, render)


def _configure_default_logging_by_custom(shared_processors: list[Any], logs_render: Any) -> None:
    handler = logging.StreamHandler()

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            logs_render,
        ],
    )

    handler.setFormatter(formatter)

    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()

        if logger_name == "uvicorn.access":
            logger.propagate = False
            continue

        logger.propagate = True

    root_uvicorn_logger = logging.getLogger()
    root_uvicorn_logger.addHandler(handler)
    root_uvicorn_logger.setLevel(logging.INFO)
