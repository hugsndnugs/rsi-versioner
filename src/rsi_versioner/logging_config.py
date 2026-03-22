from __future__ import annotations

import logging
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

from platformdirs import user_log_dir

APP_NAME = "rsi-versioner"
LOG_FILENAME = "rsi_versioner.log"
LOGGER_NAME = "rsi_versioner"


class UtcIsoFormatter(logging.Formatter):
    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created))


def log_dir_path() -> Path:
    return Path(user_log_dir(APP_NAME, appauthor=False))


def log_file_path() -> Path:
    return log_dir_path() / LOG_FILENAME


def configure_logging(
    *,
    log_dir: Path | None = None,
    max_bytes: int = 256_000,
    backup_count: int = 5,
) -> Path:
    """
    Attach a rotating file handler to the rsi_versioner logger. Safe to call once;
    subsequent calls return the log path without adding duplicate handlers.
    """
    base = log_dir if log_dir is not None else log_dir_path()
    base.mkdir(parents=True, exist_ok=True)
    path = base / LOG_FILENAME
    log = logging.getLogger(LOGGER_NAME)
    log.setLevel(logging.INFO)
    if any(isinstance(h, RotatingFileHandler) for h in log.handlers):
        return path
    fh = RotatingFileHandler(
        path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    fh.setFormatter(
        UtcIsoFormatter("%(asctime)s %(levelname)s %(message)s"),
    )
    log.addHandler(fh)
    return path
