"""
Error Handling and Recovery System

Provides robust error handling and recovery mechanisms.
"""

import logging
from typing import Optional, Callable, Any
from functools import wraps
import time

logger = logging.getLogger(__name__)


def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator to retry function on failure.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Backoff multiplier for delay
        exceptions: Tuple of exceptions to catch
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            retries = 0
            current_delay = delay
            
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries >= max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                        raise
                    
                    logger.warning(f"Function {func.__name__} failed (attempt {retries}/{max_retries}): {e}. Retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            return None
        return wrapper
    return decorator


def fallback_value(default_value: Any):
    """
    Decorator to return default value on failure.
    
    Args:
        default_value: Value to return on error
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Function {func.__name__} failed, using fallback: {e}")
                return default_value
        return wrapper
    return decorator


class ErrorRecovery:
    """
    Error recovery manager.
    """
    
    def __init__(self):
        self.recovery_strategies = {}
    
    def register_strategy(self, error_type: type, strategy: Callable):
        """
        Register recovery strategy for error type.
        
        Args:
            error_type: Exception type
            strategy: Recovery function
        """
        self.recovery_strategies[error_type] = strategy
    
    def handle_error(self, error: Exception, context: Optional[dict] = None) -> Optional[Any]:
        """
        Handle error using registered strategy.
        
        Args:
            error: Exception object
            context: Optional context dictionary
            
        Returns:
            Recovery result or None
        """
        error_type = type(error)
        
        if error_type in self.recovery_strategies:
            try:
                return self.recovery_strategies[error_type](error, context)
            except Exception as recovery_error:
                logger.error(f"Recovery strategy failed: {recovery_error}")
        
        return None


# Global error recovery instance
_error_recovery = ErrorRecovery()

def get_error_recovery() -> ErrorRecovery:
    """Get global error recovery instance."""
    return _error_recovery


# Example recovery strategies
def model_load_fallback(error: Exception, context: dict) -> dict:
    """Fallback when model fails to load."""
    logger.warning("Model load failed, using default predictions")
    return {
        "predicted_lap_time": 95.0,
        "confidence": 0.5,
        "fallback": True
    }

def api_timeout_fallback(error: Exception, context: dict) -> dict:
    """Fallback when API times out."""
    logger.warning("API timeout, using cached/default data")
    return {
        "success": False,
        "error": "timeout",
        "fallback": True
    }

# Register default strategies
_error_recovery.register_strategy(FileNotFoundError, model_load_fallback)
_error_recovery.register_strategy(TimeoutError, api_timeout_fallback)

