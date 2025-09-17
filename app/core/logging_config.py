"""
Logging configuration for the QR Code Ordering System

This module provides comprehensive logging setup with structured logging,
error monitoring, and different log levels for development and production.
"""

import logging
import logging.config
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from app.core.config import settings


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Create base log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info) if record.exc_info else None
            }
        
        # Add extra fields from the log record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                'thread', 'threadName', 'processName', 'process', 'getMessage', 'exc_info',
                'exc_text', 'stack_info', 'message'
            }:
                extra_fields[key] = value
        
        if extra_fields:
            log_entry["extra"] = extra_fields
        
        return json.dumps(log_entry, default=str, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output in development"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        # Add color to level name
        level_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{level_color}{record.levelname}{self.RESET}"
        
        # Format the message
        formatted = super().format(record)
        
        # Add extra fields if present
        extra_info = []
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                'thread', 'threadName', 'processName', 'process', 'getMessage', 'exc_info',
                'exc_text', 'stack_info', 'message'
            } and not key.startswith('color_'):
                extra_info.append(f"{key}={value}")
        
        if extra_info:
            formatted += f" | {' | '.join(extra_info)}"
        
        return formatted


def setup_logging():
    """Setup logging configuration based on environment"""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Base logging configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "structured": {
                "()": StructuredFormatter,
            },
            "colored": {
                "()": ColoredFormatter,
                "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "simple": {
                "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG" if settings.debug else "INFO",
                "formatter": "colored" if settings.debug else "simple",
                "stream": sys.stdout
            },
            "file_info": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "structured",
                "filename": log_dir / "app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8"
            },
            "file_error": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "structured",
                "filename": log_dir / "error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,
                "encoding": "utf8"
            },
            "security": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "WARNING",
                "formatter": "structured",
                "filename": log_dir / "security.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,
                "encoding": "utf8"
            }
        },
        "loggers": {
            # Application loggers
            "app": {
                "level": "DEBUG" if settings.debug else "INFO",
                "handlers": ["console", "file_info", "file_error"],
                "propagate": False
            },
            # Security logger for authentication/authorization events
            "app.security": {
                "level": "WARNING",
                "handlers": ["console", "security", "file_error"],
                "propagate": False
            },
            # Database logger
            "app.database": {
                "level": "INFO",
                "handlers": ["console", "file_info", "file_error"],
                "propagate": False
            },
            # External services logger
            "app.external": {
                "level": "INFO",
                "handlers": ["console", "file_info", "file_error"],
                "propagate": False
            },
            # FastAPI and Uvicorn loggers
            "fastapi": {
                "level": "INFO",
                "handlers": ["console", "file_info"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console", "file_info"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["file_info"],
                "propagate": False
            },
            # Supabase logger
            "supabase": {
                "level": "WARNING",
                "handlers": ["console", "file_info"],
                "propagate": False
            }
        },
        "root": {
            "level": "INFO",
            "handlers": ["console", "file_info", "file_error"]
        }
    }
    
    # Apply the configuration
    logging.config.dictConfig(config)
    
    # Set up specific logger levels for third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.INFO)
    
    # Create application logger
    logger = logging.getLogger("app")
    logger.info("Logging configuration initialized", extra={
        "debug_mode": settings.debug,
        "log_level": "DEBUG" if settings.debug else "INFO"
    })
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return logging.getLogger(f"app.{name}")


def log_request_info(
    logger: logging.Logger,
    method: str,
    url: str,
    status_code: int,
    duration_ms: float,
    user_id: Optional[str] = None,
    restaurant_id: Optional[str] = None,
    **extra_fields
):
    """Log request information with structured data"""
    logger.info(
        f"{method} {url} - {status_code} ({duration_ms:.2f}ms)",
        extra={
            "request_method": method,
            "request_url": url,
            "response_status": status_code,
            "duration_ms": duration_ms,
            "user_id": user_id,
            "restaurant_id": restaurant_id,
            **extra_fields
        }
    )


def log_security_event(
    event_type: str,
    message: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    **extra_fields
):
    """Log security-related events"""
    security_logger = logging.getLogger("app.security")
    security_logger.warning(
        message,
        extra={
            "security_event": event_type,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            **extra_fields
        }
    )


def log_database_operation(
    operation: str,
    table: str,
    duration_ms: float,
    success: bool = True,
    error: Optional[str] = None,
    **extra_fields
):
    """Log database operations"""
    db_logger = logging.getLogger("app.database")
    
    if success:
        db_logger.info(
            f"Database {operation} on {table} completed ({duration_ms:.2f}ms)",
            extra={
                "db_operation": operation,
                "db_table": table,
                "duration_ms": duration_ms,
                "success": success,
                **extra_fields
            }
        )
    else:
        db_logger.error(
            f"Database {operation} on {table} failed ({duration_ms:.2f}ms): {error}",
            extra={
                "db_operation": operation,
                "db_table": table,
                "duration_ms": duration_ms,
                "success": success,
                "error": error,
                **extra_fields
            }
        )


def log_external_service_call(
    service: str,
    operation: str,
    duration_ms: float,
    success: bool = True,
    status_code: Optional[int] = None,
    error: Optional[str] = None,
    **extra_fields
):
    """Log external service calls"""
    external_logger = logging.getLogger("app.external")
    
    if success:
        external_logger.info(
            f"External service call to {service}.{operation} completed ({duration_ms:.2f}ms)",
            extra={
                "external_service": service,
                "operation": operation,
                "duration_ms": duration_ms,
                "success": success,
                "status_code": status_code,
                **extra_fields
            }
        )
    else:
        external_logger.error(
            f"External service call to {service}.{operation} failed ({duration_ms:.2f}ms): {error}",
            extra={
                "external_service": service,
                "operation": operation,
                "duration_ms": duration_ms,
                "success": success,
                "status_code": status_code,
                "error": error,
                **extra_fields
            }
        )


# Context manager for logging operation duration
class LogOperationTime:
    """Context manager to log operation duration"""
    
    def __init__(
        self,
        logger: logging.Logger,
        operation: str,
        level: int = logging.INFO,
        **extra_fields
    ):
        self.logger = logger
        self.operation = operation
        self.level = level
        self.extra_fields = extra_fields
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (datetime.utcnow() - self.start_time).total_seconds() * 1000
            
            if exc_type is None:
                self.logger.log(
                    self.level,
                    f"{self.operation} completed ({duration:.2f}ms)",
                    extra={
                        "operation": self.operation,
                        "duration_ms": duration,
                        "success": True,
                        **self.extra_fields
                    }
                )
            else:
                self.logger.error(
                    f"{self.operation} failed ({duration:.2f}ms): {exc_val}",
                    extra={
                        "operation": self.operation,
                        "duration_ms": duration,
                        "success": False,
                        "error_type": exc_type.__name__ if exc_type else None,
                        "error_message": str(exc_val) if exc_val else None,
                        **self.extra_fields
                    }
                )


# Initialize logging when module is imported
setup_logging()