"""Structured logging configuration using structlog.

Provides console-based structured logging with colored output for readability.
Can easily be switched to JSON format for production environments.
"""

import structlog
from structlog.processors import JSONRenderer
from structlog.dev import ConsoleRenderer


def configure_logging(use_json: bool = False):
    """Configure structlog for console or JSON output.

    Args:
        use_json: If True, output JSON logs. If False, use colored console output.
    """
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if use_json:
        processors.append(JSONRenderer())
    else:
        processors.append(ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None):
    """Get a configured structlog logger.

    Args:
        name: Optional logger name for identification.

    Returns:
        Configured structlog logger instance.
    """
    if name:
        return structlog.get_logger(name)
    return structlog.get_logger()


# Configure logging on module import (console output by default)
configure_logging(use_json=False)
