import logging

from app.infrastructure.observability import StructuredJsonFormatter


def configure_logging(level: str) -> None:
    """Configure structured application logging without removing host handlers."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level))
    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredJsonFormatter())
        root.addHandler(handler)
        return
    for handler in root.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setFormatter(StructuredJsonFormatter())
