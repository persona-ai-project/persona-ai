"""
logging_config.py
=================
Structured logging configuration for production.
"""
import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import Any


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data
        
        # Add exception info
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }
        
        # Add request context if available
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        
        return json.dumps(log_entry, default=str)


class ConsoleFormatter(logging.Formatter):
    """Colored console formatter for development."""
    
    COLORS = {
        "DEBUG": "\033[36m",    # Cyan
        "INFO": "\033[32m",     # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",    # Red
        "CRITICAL": "\033[35m", # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        
        return (
            f"{color}[{record.levelname}]{self.RESET} "
            f"{record.name}: {record.getMessage()}"
        )


def setup_logging(
    level: str = "INFO",
    json_output: bool = None,
    log_file: str = None,
) -> None:
    """
    Setup structured logging.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: Use JSON format (default: True in production)
        log_file: Optional log file path
    """
    if json_output is None:
        json_output = os.getenv("ENVIRONMENT", "development") == "production"
    
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    if json_output:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(ConsoleFormatter())
    
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)
    
    # Suppress noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    logging.info(f"Logging initialized: level={level}, json={json_output}")


def get_logger(name: str) -> logging.Logger:
    """Get a named logger."""
    return logging.getLogger(name)


class RequestLogger:
    """Context logger for request tracking."""
    
    def __init__(self, request_id: str, user_id: str = None):
        self.request_id = request_id
        self.user_id = user_id
        self.logger = logging.getLogger("request")
    
    def _log(self, level: str, message: str, extra: dict = None):
        record = self.logger.makeRecord(
            self.logger.name,
            getattr(logging, level),
            "",
            0,
            message,
            (),
            None,
        )
        record.request_id = self.request_id
        if self.user_id:
            record.user_id = self.user_id
        if extra:
            record.extra_data = extra
        self.logger.handle(record)
    
    def info(self, message: str, **kwargs):
        self._log("INFO", message, kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log("WARNING", message, kwargs)
    
    def error(self, message: str, **kwargs):
        self._log("ERROR", message, kwargs)
    
    def debug(self, message: str, **kwargs):
        self._log("DEBUG", message, kwargs)
