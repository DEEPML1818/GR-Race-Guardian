"""
Stability Layer

Provides comprehensive error handling, logging, data validation, and auto-recovery.
"""

import logging
import traceback
import sys
import os
from typing import Dict, Optional, Any, Callable, List, Tuple

from datetime import datetime
import signal
import subprocess
import time
from pathlib import Path

from .logger import get_logger, log_error
from .error_handler import retry_on_failure, fallback_value, get_error_recovery
from .data_validator import get_validator

logger = get_logger(__name__)


class StabilityLayer:
    """
    Comprehensive stability layer for error handling, logging, and recovery.
    """
    
    def __init__(self):
        self.logger = logger
        self.validator = get_validator()
        self.error_recovery = get_error_recovery()
        self.crash_count = 0
        self.max_crash_restarts = 5
        self.restart_delay = 5.0
        
        # Setup crash handlers
        self._setup_crash_handlers()
    
    def _setup_crash_handlers(self):
        """Setup signal handlers for graceful shutdown and crash recovery."""
        def signal_handler(signum, frame):
            self.logger.warning(f"Received signal {signum}, initiating graceful shutdown...")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Handle uncaught exceptions
        def exception_handler(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            error_msg = f"Uncaught exception: {exc_type.__name__}: {exc_value}"
            self.log_error(
                Exception(error_msg),
                context={
                    "type": exc_type.__name__,
                    "traceback": traceback.format_exception(exc_type, exc_value, exc_traceback)
                }
            )
            
            # Attempt recovery
            self._attempt_recovery(exc_type, exc_value)
        
        sys.excepthook = exception_handler
    
    def log_error(self, error: Exception, context: Optional[Dict] = None, level: str = "ERROR"):
        """
        Enhanced error logging with full context.
        """
        error_context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.utcnow().isoformat(),
            "traceback": traceback.format_exc()
        }
        
        if context:
            error_context.update(context)
        
        if level == "CRITICAL":
            self.logger.critical(f"CRITICAL ERROR: {error}", extra=error_context)
        else:
            self.logger.error(f"ERROR: {error}", extra=error_context)
        
        # Also log to error file
        self._log_to_error_file(error, error_context)
    
    def _log_to_error_file(self, error: Exception, context: Dict):
        """Log critical errors to dedicated error file."""
        error_log_dir = Path("logs/errors")
        error_log_dir.mkdir(parents=True, exist_ok=True)
        
        error_log_file = error_log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
        
        with open(error_log_file, "a") as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"ERROR: {datetime.now().isoformat()}\n")
            f.write(f"Type: {context.get('error_type')}\n")
            f.write(f"Message: {context.get('error_message')}\n")
            f.write(f"Traceback:\n{context.get('traceback', 'N/A')}\n")
            if context.get('context'):
                f.write(f"Context: {context.get('context')}\n")
            f.write(f"{'='*80}\n")
    
    def validate_data(self, data: Dict, request_type: str) -> Tuple[bool, List[str], List[str]]:
        """
        Validate input data.
        
        Returns:
            (is_valid, errors, warnings)
        """
        return self.validator.validate_all(data, request_type)
    
    def handle_api_error(self, error: Exception, endpoint: str, context: Optional[Dict] = None) -> Dict:
        """
        Handle API errors with logging and recovery.
        """
        self.log_error(error, context={
            "endpoint": endpoint,
            "context": context
        })
        
        # Attempt recovery
        recovery_result = self.error_recovery.handle_error(error, context)
        
        if recovery_result:
            return {
                "success": False,
                "error": str(error),
                "recovered": True,
                "fallback_data": recovery_result
            }
        
        return {
            "success": False,
            "error": str(error),
            "recovered": False
        }
    
    def _attempt_recovery(self, exc_type, exc_value):
        """Attempt to recover from uncaught exceptions."""
        self.crash_count += 1
        
        if self.crash_count >= self.max_crash_restarts:
            self.logger.critical(
                f"Maximum crash restarts ({self.max_crash_restarts}) reached. "
                "System will not auto-restart."
            )
            return
        
        self.logger.warning(
            f"Crash detected (count: {self.crash_count}/{self.max_crash_restarts}). "
            f"Attempting recovery in {self.restart_delay}s..."
        )
        
        # In production, this would trigger a restart
        # For now, just log the recovery attempt
        time.sleep(self.restart_delay)
    
    def check_data_quality(self, data: Dict, data_type: str) -> Dict:
        """
        Check data quality and completeness.
        
        Returns:
            Quality report with warnings and suggestions
        """
        report = {
            "quality_score": 1.0,
            "warnings": [],
            "suggestions": []
        }
        
        if data_type == "driver_twin":
            lap_times = data.get("lap_times", [])
            if len(lap_times) < 5:
                report["quality_score"] -= 0.2
                report["warnings"].append("Less than 5 lap times - reduced accuracy")
                report["suggestions"].append("Provide more lap times for better analysis")
            
            if not data.get("sector_times"):
                report["quality_score"] -= 0.1
                report["warnings"].append("No sector times provided")
                report["suggestions"].append("Include sector times for detailed analysis")
        
        elif data_type == "race_twin":
            drivers = data.get("drivers", [])
            if len(drivers) < 3:
                report["quality_score"] -= 0.2
                report["warnings"].append("Less than 3 drivers - limited race simulation")
                report["suggestions"].append("Include more drivers for realistic simulation")
        
        report["quality_score"] = max(0.0, report["quality_score"])
        
        return report


# Global stability layer instance
_stability_layer = None

def get_stability_layer() -> StabilityLayer:
    """Get global stability layer instance."""
    global _stability_layer
    if _stability_layer is None:
        _stability_layer = StabilityLayer()
    return _stability_layer

