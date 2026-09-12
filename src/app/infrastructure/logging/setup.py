import logging

from app.infrastructure.observability import StructuredJsonFormatter


def configure_logging(level: str) -> None:
    """Configure structured application logging without removing host handlers."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level))
    if not root.handlers:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(StructuredJsonFormatter())
        root.addHandler(stream_handler)
        return
    for root_handler in root.handlers:
        if isinstance(root_handler, logging.StreamHandler):
            root_handler.setFormatter(StructuredJsonFormatter())
