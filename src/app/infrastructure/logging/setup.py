import logging

from app.infrastructure.observability import StructuredJsonFormatter


def configure_logging(level: str) -> None:
    """Configure one predictable application-wide structured logging policy."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level))
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredJsonFormatter())
    root.handlers.clear()
    root.addHandler(handler)
