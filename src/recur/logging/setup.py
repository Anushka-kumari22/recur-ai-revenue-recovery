import logging
import sys

from recur.config import get_settings


def configure_logging() -> None:
    """
    Configure centralized application logging.

    This function should be called once during application
    startup before processing requests or batch jobs.
    """

    settings = get_settings()

    log_level = getattr(
        logging,
        settings.log_level.upper(),
        logging.INFO,
    )

    logging.basicConfig(
        level=log_level,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(
                sys.stdout,
            ),
        ],
        force=True,
    )