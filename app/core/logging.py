"""
Logging Configuration Module

Provides enterprise-grade logging with:
- Console output (INFO and above)
- File logging with rotation (DEBUG and above)
- Structured logging support
- Performance metrics
- Error tracking
- Context preservation
"""

import os
import sys
from pathlib import Path
from loguru import logger
from datetime import datetime

# -------------------------------------------------
# LOGGING CONFIGURATION
# -------------------------------------------------

# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Get environment
ENV = os.getenv("APP_ENV", "dev")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Log file paths
LOG_FILE = LOGS_DIR / "app.log"
ERROR_LOG_FILE = LOGS_DIR / "error.log"
DEBUG_LOG_FILE = LOGS_DIR / "debug.log"

# Format strings
STANDARD_FORMAT = (
    "<level>{time:YYYY-MM-DD HH:mm:ss.SSS}</level> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

JSON_FORMAT = (
    '{{"time": "{time:YYYY-MM-DD HH:mm:ss.SSS}", '
    '"level": "{level}", '
    '"logger": "{name}", '
    '"function": "{function}", '
    '"line": {line}, '
    '"message": "{message}"}}'
)

# -------------------------------------------------
# REMOVE DEFAULT HANDLER
# -------------------------------------------------

logger.remove()


# -------------------------------------------------
# CONSOLE HANDLER (INFO and above)
# -------------------------------------------------

logger.add(
    sys.stdout,
    level=LOG_LEVEL,
    format=STANDARD_FORMAT,
    colorize=True,
    backtrace=True,
    diagnose=True,
)


# -------------------------------------------------
# FILE HANDLER (DEBUG and above)
# -------------------------------------------------

logger.add(
    str(LOG_FILE),
    level="DEBUG",
    format=STANDARD_FORMAT,
    rotation="500 MB",  # Rotate when file reaches 500MB
    retention="7 days",  # Keep logs for 7 days
    compression="zip",  # Compress rotated logs
    backtrace=True,
    diagnose=True,
)


# -------------------------------------------------
# ERROR FILE HANDLER (ERROR and above)
# -------------------------------------------------

logger.add(
    str(ERROR_LOG_FILE),
    level="ERROR",
    format=STANDARD_FORMAT,
    rotation="100 MB",
    retention="30 days",
    compression="zip",
    backtrace=True,
    diagnose=True,
)


# -------------------------------------------------
# DEBUG FILE HANDLER (DEBUG - for development)
# -------------------------------------------------

if ENV == "dev":
    logger.add(
        str(DEBUG_LOG_FILE),
        level="DEBUG",
        format=STANDARD_FORMAT,
        rotation="50 MB",
        retention="3 days",
        backtrace=True,
        diagnose=True,
    )


# -------------------------------------------------
# CONTEXT AND EXTRA DATA
# -------------------------------------------------

def bind_context(**kwargs):
    """
    Bind context data to all subsequent logs.
    
    Usage:
        bind_context(user_id=123, request_id="abc123")
    """
    return logger.bind(**kwargs)


def get_logger(name: str = None):
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name (usually __name__ from calling module)
    
    Returns:
        Configured logger instance
    """
    if name:
        return logger.bind(logger_name=name)
    return logger


# -------------------------------------------------
# CONVENIENCE FUNCTIONS
# -------------------------------------------------

def log_startup_info():
    """Log application startup information."""
    logger.info("=" * 80)
    logger.info("AI RAG Sentiment Bot - Startup")
    logger.info("=" * 80)
    logger.info(f"Environment: {ENV}")
    logger.info(f"Log Level: {LOG_LEVEL}")
    logger.info(f"Logs Directory: {LOGS_DIR}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("=" * 80)


def log_shutdown_info():
    """Log application shutdown information."""
    logger.info("=" * 80)
    logger.info("AI RAG Sentiment Bot - Shutdown")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("=" * 80)


def log_performance(operation: str, duration: float):
    """
    Log performance metrics.
    
    Args:
        operation: Operation name
        duration: Duration in seconds
    """
    if duration > 1.0:
        logger.warning(f"SLOW OPERATION: {operation} took {duration:.2f}s")
    else:
        logger.debug(f"Performance: {operation} completed in {duration:.3f}s")


def log_database_query(query: str, duration: float, rows: int = None):
    """
    Log database query execution.
    
    Args:
        query: SQL query
        duration: Execution time in seconds
        rows: Number of rows affected
    """
    if duration > 0.5:
        logger.warning(
            f"SLOW QUERY: Execution time {duration:.3f}s, Rows: {rows}"
        )
    else:
        logger.debug(
            f"Query executed in {duration:.3f}s, Rows: {rows}"
        )


def log_api_request(method: str, path: str, status_code: int, duration: float):
    """
    Log API request.
    
    Args:
        method: HTTP method
        path: Request path
        status_code: Response status code
        duration: Request duration in seconds
    """
    status_symbol = "✅" if status_code < 400 else "❌"
    logger.info(
        f"{status_symbol} {method} {path} - {status_code} ({duration:.3f}s)"
    )


def log_error_with_context(error: Exception, context: dict = None):
    """
    Log error with additional context.
    
    Args:
        error: Exception object
        context: Additional context dict
    """
    context_str = f"\nContext: {context}" if context else ""
    logger.error(f"{type(error).__name__}: {str(error)}{context_str}", exc_info=True)


def log_sentiment_analysis(text: str, score: float, label: str):
    """
    Log sentiment analysis result.
    
    Args:
        text: Analyzed text (truncated)
        score: Sentiment score
        label: Sentiment label
    """
    text_preview = text[:50] + "..." if len(text) > 50 else text
    logger.debug(
        f"Sentiment: {label.upper()} (score: {score:.3f}) - {text_preview}"
    )


def log_escalation(conversation_id: int, reason: str, severity: str = "medium"):
    """
    Log escalation event.
    
    Args:
        conversation_id: Conversation ID
        reason: Escalation reason
        severity: Severity level (low, medium, high, critical)
    """
    logger.warning(
        f"ESCALATION [severity={severity}] - "
        f"Conversation {conversation_id}: {reason}"
    )


# -------------------------------------------------
# INITIALIZATION
# -------------------------------------------------

# Log startup information
log_startup_info()

# Export logger for convenience imports
__all__ = [
    "logger",
    "get_logger",
    "bind_context",
    "log_startup_info",
    "log_shutdown_info",
    "log_performance",
    "log_database_query",
    "log_api_request",
    "log_error_with_context",
    "log_sentiment_analysis",
    "log_escalation",
]
