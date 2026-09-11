import logging

from app.config.settings import get_settings
from app.infrastructure.logging.setup import configure_logging

logger = logging.getLogger(__name__)


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("Application configuration validated")
    logger.info("Starting %s in %s mode", settings.app_name, settings.app_env)


if __name__ == "__main__":
    main()
