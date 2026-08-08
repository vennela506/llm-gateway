import logging
import structlog


def setup_logging():
    """Configures structured JSON logging for the application."""

    # Set the standard logging level
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
    )

    # Configure structlog to output JSON
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


# Export a configured logger instance
logger = structlog.get_logger("llm_gateway")
