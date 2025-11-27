"""
Unified Logging System for GR Race Guardian

Provides structured logging for Python backend.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_dir: str = "logs"
) -> logging.Logger:
    """
    Setup unified logging system.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file name (default: auto-generated)
        log_dir: Directory for log files
        
    Returns:
        Configured logger
    """
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Generate log file name if not provided
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"race_guardian_{timestamp}.log"
    
    log_file_path = log_path / log_file
    
    # Configure logging format
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Root logger
    logger = logging.getLogger('gr_race_guardian')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)
    
    logger.info(f"Logging initialized - Level: {log_level}, File: {log_file_path}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get logger for a specific module.
    
    Args:
        name: Module name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f'gr_race_guardian.{name}')


# Error logging helpers
def log_error(logger: logging.Logger, error: Exception, context: Optional[dict] = None):
    """
    Log error with context.
    
    Args:
        logger: Logger instance
        error: Exception object
        context: Optional context dictionary
    """
    error_msg = f"Error: {type(error).__name__}: {str(error)}"
    if context:
        error_msg += f" | Context: {context}"
    logger.error(error_msg, exc_info=True)


def log_api_call(logger: logging.Logger, endpoint: str, method: str, status: int, duration: float):
    """
    Log API call details.
    
    Args:
        logger: Logger instance
        endpoint: API endpoint
        method: HTTP method
        status: Response status code
        duration: Request duration in seconds
    """
    logger.info(f"API {method} {endpoint} - Status: {status} - Duration: {duration:.3f}s")


if __name__ == "__main__":
    # Test logging
    logger = setup_logging(log_level="DEBUG")
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")

