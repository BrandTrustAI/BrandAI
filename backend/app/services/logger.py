"""
Logging service for BrandAI application.
Configures structured logging with file and console output.
"""
import sys
from pathlib import Path
from loguru import logger

from app.config import settings


def setup_logger():
    """
    Configure and setup application logger.
    
    Sets up:
    - Console logging with colored output
    - File logging to logs directory
    - Log rotation and retention
    - Structured logging format
    """
    # Remove default logger
    logger.remove()
    
    # Log format
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Console logging
    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.LOG_LEVEL,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # File logging
    log_dir = Path(__file__).parent.parent.parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "brandai.log"
    error_log_file = log_dir / "brandai_errors.log"
    
    # General log file
    logger.add(
        log_file,
        format=log_format,
        level=settings.LOG_LEVEL,
        rotation="10 MB",  # Rotate when file reaches 10MB
        retention="7 days",  # Keep logs for 7 days
        compression="zip",  # Compress old logs
        backtrace=True,
        diagnose=True,
        enqueue=True  # Thread-safe logging
    )
    
    # Error log file (only errors and above)
    logger.add(
        error_log_file,
        format=log_format,
        level="ERROR",
        rotation="10 MB",
        retention="30 days",  # Keep error logs longer
        compression="zip",
        backtrace=True,
        diagnose=True,
        enqueue=True
    )
    
    return logger


# Initialize logger
app_logger = setup_logger()

# Export logger for easy import
__all__ = ["app_logger", "setup_logger"]
