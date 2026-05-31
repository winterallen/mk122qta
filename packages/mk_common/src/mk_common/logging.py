from __future__ import annotations

import logging
from typing import Any, cast

import structlog


def configure_logging(*, service: str, level: int = logging.INFO) -> None:
    logging.basicConfig(level=level, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(sort_keys=True),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(service=service)


def get_logger(name: str | None = None, **context: Any) -> structlog.BoundLogger:
    logger = structlog.get_logger(name)
    if context:
        return cast(structlog.BoundLogger, logger.bind(**context))
    return cast(structlog.BoundLogger, logger)
