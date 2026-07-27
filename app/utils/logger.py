"""
Professional logging setup for the application.

Provides a single `configure_logging()` call, made once at startup from
`app/main.py`, which attaches:

    - A `TimedRotatingFileHandler` that rolls over to a new file every
      midnight and keeps `AppConfig.log_retention_days` days of history,
      writing to `logs/app.log`, `logs/app.log.2026-07-07`, etc.
    - A `StreamHandler` for console output during development.

After calling `configure_logging()` once, every module in the codebase
should simply do:

    import logging
    logger = logging.getLogger(__name__)

and log normally; there is no need to touch handlers again.
"""

from __future__ import annotations

import logging
import logging.handlers
import sys

from app.config.app_config import get_config

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def configure_logging() -> None:
    """Configure the root logger. Safe to call more than once (idempotent)."""
    global _configured
    if _configured:
        return

    config = get_config()
    config.logs_dir.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(config.log_level)

    formatter = logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT)

    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=str(config.logs_dir / "app.log"),
        when="midnight",
        interval=1,
        backupCount=config.log_retention_days,
        encoding="utf-8",
        utc=False,
    )
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setFormatter(formatter)
    file_handler.setLevel(config.log_level)

    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(config.log_level)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Third-party libraries can be noisy at INFO/DEBUG; keep them at WARNING
    # unless the developer explicitly enables debug mode.
    if not config.debug:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    _configured = True
    logging.getLogger(__name__).info(
        "Logging configured. Level=%s, dir=%s", config.log_level, config.logs_dir
    )
