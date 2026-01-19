from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string."""
        payload: Dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
        }
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
            }:
                if key not in payload:
                    payload[key] = value
        return json.dumps(payload, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    def __init__(self):
        super().__init__(fmt="%(levelname)s: %(name)s: %(message)s")

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        extras = []
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "asctime",
                "message",
            }:
                extras.append(f"{key}={value}")
        if extras:
            message += " " + " ".join(extras)
        return message


class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"

    def __init__(self):
        super().__init__(fmt="%(levelname)s: %(name)s: %(message)s")

    def format(self, record: logging.LogRecord) -> str:
        levelname = record.levelname
        level_color = self.COLORS.get(levelname, "")
        original_levelname = record.levelname
        record.levelname = f"{level_color}{levelname}{self.RESET}"
        message = super().format(record)
        record.levelname = original_levelname
        extras = []
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "asctime",
                "message",
            }:
                extras.append(f"{key}={value}")
        if extras:
            message += " " + " ".join(extras)
        return message


def get_formatter(format_type: str) -> logging.Formatter:
    """Get formatter instance based on format type."""
    if format_type == "json":
        return JsonFormatter()
    if format_type == "colored":
        return ColoredFormatter()
    return TextFormatter()


def setup_logging(
    level: str = "INFO",
    format: str = "json",
    log_file: str | None = None,
) -> None:
    """Configure root logger with file or console output."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(log_level)

    # for h in list(root.handlers):
    #     root.removeHandler(h)

    # for name in list(logging.Logger.manager.loggerDict.keys()):
    #     logger = logging.getLogger(name)
    #     for h in list(logger.handlers):
    #         logger.removeHandler(h)
    #     logger.propagate = True
    #     logger.setLevel(logging.NOTSET)

    # logging.disable(logging.NOTSET)
    #
    sql_logger = logging.getLogger("sqlalchemy.engine.Engine")
    sql_logger.propagate = False  # Prevent logs from doubling up in the root logger

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(get_formatter(format))
        root.addHandler(file_handler)
        sql_logger.addHandler(file_handler)
    else:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(get_formatter(format))
        root.addHandler(console_handler)
        sql_logger.addHandler(console_handler)


def get_logger(name: str | None = None) -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(name or "app")


def get_logging_config(
    level: str = "INFO", format: str = "json", log_file: str | None = None
) -> dict:
    """Get uvicorn logging configuration."""
    formatter_class = (
        "app.logger.JsonFormatter"
        if format == "json"
        else (
            "app.logger.ColoredFormatter"
            if format == "colored"
            else "app.logger.TextFormatter"
        )
    )
    handler_config = {
        "formatter": "default",
        "class": "logging.FileHandler" if log_file else "logging.StreamHandler",
    }
    if log_file:
        handler_config["filename"] = log_file

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": formatter_class,
            },
        },
        "handlers": {
            "default": handler_config,
        },
        "loggers": {
            "": {
                "handlers": ["default"],
                "level": level,
            },
        },
    }
