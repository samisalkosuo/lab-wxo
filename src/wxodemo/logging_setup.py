"""Friendly console output plus a detailed rotating log file, with secrets masked."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOGGER_NAME = "wxodemo"
_MASK = "****"
_secrets: set[str] = set()


def register_secret(value: str) -> None:
    """Make sure `value` never shows up on the console or in the log file."""
    if value and len(value) >= 4:
        _secrets.add(value)


def mask(text: str) -> str:
    for secret in sorted(_secrets, key=len, reverse=True):
        text = text.replace(secret, _MASK)
    return text


class _MaskFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = mask(record.getMessage())
        record.args = None
        return True


def _supports_unicode() -> bool:
    encoding = getattr(sys.stdout, "encoding", None) or ""
    try:
        "\u2713\u2717".encode(encoding or "ascii")
    except (UnicodeEncodeError, LookupError):
        return False
    return True


class _ConsoleFormatter(logging.Formatter):
    def __init__(self) -> None:
        super().__init__("%(message)s")
        if _supports_unicode():
            self._marks = {"ok": "\u2713", "fail": "\u2717", "warn": "!", "info": "-"}
        else:
            self._marks = {"ok": "[ok]", "fail": "[x]", "warn": "[!]", "info": "-"}

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        mark = getattr(record, "mark", None)
        if mark is None and record.levelno >= logging.ERROR:
            mark = "fail"
        elif mark is None and record.levelno == logging.WARNING:
            mark = "warn"
        if mark is None or record.levelno < logging.INFO:
            return message
        return f"{self._marks[mark]} {message}"


class _StdoutHandler(logging.StreamHandler):
    """Writes to whatever sys.stdout is at the time of each message (like logging's stderr one)."""

    def __init__(self) -> None:
        logging.Handler.__init__(self)

    @property
    def stream(self):
        return sys.stdout


def setup_logging(log_file: Path, verbose: bool = False) -> logging.Logger:
    """Console gets short INFO lines (DEBUG with verbose); the file gets everything."""
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)

    # Never crash on a character the console cannot encode (agent descriptions can hold any text).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    console = _StdoutHandler()
    console.setLevel(logging.DEBUG if verbose else logging.INFO)
    console.setFormatter(_ConsoleFormatter())
    console.addFilter(_MaskFilter())
    logger.addHandler(console)

    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)-7s %(message)s", "%Y-%m-%d %H:%M:%S")
    )
    file_handler.addFilter(_MaskFilter())
    logger.addHandler(file_handler)
    return logger


def get_logger() -> logging.Logger:
    return logging.getLogger(LOGGER_NAME)


def info(message: str) -> None:
    get_logger().info(message, extra={"mark": "info"})


def ok(message: str) -> None:
    get_logger().info(message, extra={"mark": "ok"})


def warn(message: str) -> None:
    get_logger().warning(message)


def fail(message: str) -> None:
    get_logger().error(message)


def plain(message: str) -> None:
    """A console line without a status mark."""
    get_logger().info(message)
