import logging
import sys
from typing import Any, Dict

import structlog


def setup_logging() -> None:
    """Configure structured logging"""

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Add JSON renderer for production
    if structlog.is_configured():
        # Development setup
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    else:
        # Production setup
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


class LoggerMixin:
    """Mixin to add structured logging to classes"""

    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """Get structured logger for this class"""
        return structlog.get_logger(self.__class__.__module__, self.__class__.__name__)