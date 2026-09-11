import logging


def configure_logging(level: str) -> None:
    """Configure one predictable application-wide logging policy."""
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
