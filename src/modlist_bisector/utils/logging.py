"""https://github.com/hexdoc-dev/hexdoc/blob/9dfa14e9e0/src/hexdoc/utils/logging.py"""

import logging
from bisect import bisect
from logging import (
    Formatter,
    LogRecord,
    StreamHandler,
)
from typing import Any, Literal, Mapping, override

TRACE = 5
"""For even more verbose logs than `logging.DEBUG`."""


logger = logging.getLogger(__name__)


# https://stackoverflow.com/a/68154386
class LevelFormatter(Formatter):
    def __init__(
        self,
        formats: dict[int, str],
        datefmt: str | None = None,
        style: Literal["%", "{", "$"] = "%",
        validate: bool = True,
        *,
        defaults: Mapping[str, Any] | None = None,
    ):
        super().__init__()

        self.formats = sorted(
            (
                level,
                Formatter(fmt, datefmt, style, validate, defaults=defaults),
            )
            for level, fmt in formats.items()
        )

    @override
    def format(self, record: LogRecord) -> str:
        idx = bisect(self.formats, (record.levelno,), hi=len(self.formats) - 1)
        _, formatter = self.formats[idx]
        return formatter.format(record)


# separate class so we can isinstance below
class ResumeLevelFormatter(LevelFormatter):
    pass


def setup_logging(verbosity: int, ci: bool = False):
    logging.addLevelName(TRACE, "TRACE")

    root_logger = logging.getLogger()

    if root_logger.handlers:
        for handler in root_logger.handlers:
            if isinstance(handler.formatter, ResumeLevelFormatter):
                logger.debug(f"Removing existing handler from root logger: {handler}")
                root_logger.removeHandler(handler)

    level = verbosity_log_level(verbosity)
    root_logger.setLevel(level)

    formats = {
        logging.DEBUG: log_format("relativeCreated", "levelname", "name"),
    }

    if level >= logging.INFO:
        formats |= {
            logging.INFO: log_format("levelname"),
            logging.WARNING: log_format("levelname", "name"),
        }

    if ci:
        formats |= {
            logging.WARNING: "::warning file={name},line={lineno},title={levelname}::{message}",
            logging.ERROR: "::error file={name},line={lineno},title={levelname}::{message}",
        }

    handler = StreamHandler()

    handler.setLevel(level)
    handler.setFormatter(ResumeLevelFormatter(formats, style="{"))

    root_logger.addHandler(handler)

    logger.debug("Initialized logger.")


def log_format(*names: Literal["relativeCreated", "levelname", "name"]):
    components = {
        "relativeCreated": "{relativeCreated:.02f}",
        "levelname": "{levelname}",
        "name": "{name}",
    }

    joined_components = " | ".join(components[name] for name in names)
    return "\033[1m[" + joined_components + "]\033[0m {message}"


def verbosity_log_level(verbosity: int) -> int:
    match verbosity:
        case 0:
            return logging.INFO
        case 1:
            return logging.DEBUG
        case _:
            return TRACE
