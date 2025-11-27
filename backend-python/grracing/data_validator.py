"""
Data Validity Checker

Validates input data for all API endpoints to prevent errors and ensure data quality.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataValidator:
    """
    Data validation system for race data inputs.
    """
    
    def __init__(self):
        self.validation_errors = []
        self.validation_warnings = []
    
    def validate_driver_twin_request(self, data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate Driver Twin request data.
        
        Returns:
            (is_valid, errors)
        """
        errors = []
        
        # Required fields
        if not data.get("driver_id"):
            errors.append("driver_id is required")
        
        if not data.get("lap_times") or not isinstance(data["lap_times"], list):
            errors.append("lap_times must be a non-empty list")
        elif len(data["lap_times"]) == 0:
            errors.append("lap_times cannot be empty")
        else:
            # Validate lap times are numeric and positive
            for i, lap_time in enumerate(data["lap_times"]):
                try:
                    lap_time_float = float(lap_time)
                    if lap_time_float <= 0:
                        errors.append(f"lap_times[{i}] must be positive")
                    if lap_time_float > 300:  # Sanity check: 5 minutes max
                        errors.append(f"lap_times[{i}] is unreasonably high: {lap_time_float}s")
                except (ValueError, TypeError):
                    errors.append(f"lap_times[{i}] must be a number")
        
        # Validate sector times if provided
        if data.get("sector_times"):
            if not isinstance(data["sector_times"], list):
                errors.append("sector_times must be a list")
            else:
                for i, sector_time in enumerate(data["sector_times"]):
                    if not isinstance(sector_time, dict):
                        errors.append(f"sector_times[{i}] must be a dictionary")
                    else:
                        for sector in ["S1", "S2", "S3"]:
                            if sector in sector_time:
                                try:
                                    val = float(sector_time[sector])
                                    if val <= 0:
                                        errors.append(f"sector_times[{i}].{sector} must be positive")
                                except (ValueError, TypeError):
                                    errors.append(f"sector_times[{i}].{sector} must be a number")
        
        # Validate tire compound
        valid_compounds = ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"]
        if data.get("tire_compound") and data["tire_compound"] not in valid_compounds:
            errors.append(f"tire_compound must be one of: {', '.join(valid_compounds)}")
        
        # Validate current_lap
        if data.get("current_lap") is not None:
            try:
                lap = int(data["current_lap"])
                if lap < 0:
                    errors.append("current_lap must be non-negative")
            except (ValueError, TypeError):
                errors.append("current_lap must be an integer")
        
        return len(errors) == 0, errors
    
    def validate_race_twin_request(self, data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate Race Twin request data.
        """
        errors = []
        
        if not data.get("race_id"):
            errors.append("race_id is required")
        
        if not data.get("drivers") or not isinstance(data["drivers"], list):
            errors.append("drivers must be a non-empty list")
        elif len(data["drivers"]) == 0:
            errors.append("drivers cannot be empty")
        else:
            # Validate each driver
            for i, driver in enumerate(data["drivers"]):
                if not isinstance(driver, dict):
                    errors.append(f"drivers[{i}] must be a dictionary")
                else:
                    if not driver.get("id"):
                        errors.append(f"drivers[{i}].id is required")
                    if driver.get("position") is not None:
                        try:
                            pos = int(driver["position"])
                            if pos < 1:
                                errors.append(f"drivers[{i}].position must be >= 1")
                        except (ValueError, TypeError):
                            errors.append(f"drivers[{i}].position must be an integer")
        
        # Validate total_laps
        if not data.get("total_laps"):
            errors.append("total_laps is required")
        else:
            try:
                total_laps = int(data["total_laps"])
                if total_laps < 1:
                    errors.append("total_laps must be >= 1")
                if total_laps > 200:  # Sanity check
                    errors.append("total_laps is unreasonably high")
            except (ValueError, TypeError):
                errors.append("total_laps must be an integer")
        
        # Validate current_lap
        if data.get("current_lap") is not None:
            try:
                current_lap = int(data["current_lap"])
                if current_lap < 1:
                    errors.append("current_lap must be >= 1")
                if data.get("total_laps") and current_lap > int(data["total_laps"]):
                    errors.append("current_lap cannot exceed total_laps")
            except (ValueError, TypeError):
                errors.append("current_lap must be an integer")
        
        return len(errors) == 0, errors
    
    def validate_pit_decision_request(self, data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate Pit Decision request data.
        """
        errors = []
        
        required_fields = ["race_id", "driver_id", "current_lap", "tire_age", "tire_compound", "position"]
        for field in required_fields:
            if field not in data:
                errors.append(f"{field} is required")
        
        # Validate tire_age
        if "tire_age" in data:
            try:
                tire_age = int(data["tire_age"])
                if tire_age < 0:
                    errors.append("tire_age must be non-negative")
                if tire_age > 100:  # Sanity check
                    errors.append("tire_age is unreasonably high")
            except (ValueError, TypeError):
                errors.append("tire_age must be an integer")
        
        # Validate position
        if "position" in data:
            try:
                position = int(data["position"])
                if position < 1:
                    errors.append("position must be >= 1")
            except (ValueError, TypeError):
                errors.append("position must be an integer")
        
        # Validate tire_compound
        valid_compounds = ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"]
        if "tire_compound" in data and data["tire_compound"] not in valid_compounds:
            errors.append(f"tire_compound must be one of: {', '.join(valid_compounds)}")
        
        # Validate degradation_rate if provided
        if "degradation_rate" in data:
            try:
                rate = float(data["degradation_rate"])
                if rate < 0 or rate > 0.1:
                    errors.append("degradation_rate must be between 0 and 0.1")
            except (ValueError, TypeError):
                errors.append("degradation_rate must be a number")
        
        # Validate traffic_density if provided
        if "traffic_density" in data:
            try:
                density = float(data["traffic_density"])
                if density < 0 or density > 1:
                    errors.append("traffic_density must be between 0 and 1")
            except (ValueError, TypeError):
                errors.append("traffic_density must be a number")
        
        return len(errors) == 0, errors
    
    def validate_lap_data(self, lap_data: List[Dict]) -> Tuple[bool, List[str]]:
        """
        Validate lap data array.
        """
        errors = []
        
        if not lap_data or not isinstance(lap_data, list):
            errors.append("lap_data must be a non-empty list")
            return False, errors
        
        for i, lap in enumerate(lap_data):
            if not isinstance(lap, dict):
                errors.append(f"lap_data[{i}] must be a dictionary")
                continue
            
            # Validate lap_time if present
            if "lap_time" in lap:
                try:
                    lap_time = float(lap["lap_time"])
                    if lap_time <= 0:
                        errors.append(f"lap_data[{i}].lap_time must be positive")
                except (ValueError, TypeError):
                    errors.append(f"lap_data[{i}].lap_time must be a number")
            
            # Validate lap number if present
            if "lap" in lap:
                try:
                    lap_num = int(lap["lap"])
                    if lap_num < 1:
                        errors.append(f"lap_data[{i}].lap must be >= 1")
                except (ValueError, TypeError):
                    errors.append(f"lap_data[{i}].lap must be an integer")
        
        return len(errors) == 0, errors
    
    def validate_weather_data(self, weather_data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate weather data.
        """
        errors = []
        
        if not isinstance(weather_data, dict):
            errors.append("weather_data must be a dictionary")
            return False, errors
        
        # Validate temperature if present
        if "track_temp" in weather_data:
            try:
                temp = float(weather_data["track_temp"])
                if temp < -50 or temp > 60:  # Sanity check
                    errors.append("track_temp must be between -50 and 60°C")
            except (ValueError, TypeError):
                errors.append("track_temp must be a number")
        
        # Validate condition if present
        valid_conditions = ["dry", "wet", "damp", "rain", "snow"]
        if "condition" in weather_data:
            condition = weather_data["condition"].lower()
            if condition not in valid_conditions:
                errors.append(f"condition must be one of: {', '.join(valid_conditions)}")
        
        return len(errors) == 0, errors
    
    def validate_all(self, data: Dict, request_type: str) -> Tuple[bool, List[str], List[str]]:
        """
        Validate data based on request type.
        
        Returns:
            (is_valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        if request_type == "driver_twin":
            is_valid, errors = self.validate_driver_twin_request(data)
        elif request_type == "race_twin":
            is_valid, errors = self.validate_race_twin_request(data)
        elif request_type == "pit_decision":
            is_valid, errors = self.validate_pit_decision_request(data)
        else:
            is_valid = False
            errors.append(f"Unknown request type: {request_type}")
        
        # Additional warnings
        if request_type == "driver_twin" and data.get("lap_times"):
            if len(data["lap_times"]) < 3:
                warnings.append("Less than 3 lap times provided - analysis may be less accurate")
        
        if request_type == "race_twin" and data.get("drivers"):
            if len(data["drivers"]) < 2:
                warnings.append("Less than 2 drivers provided - race simulation may be less meaningful")
        
        return is_valid, errors, warnings


# Global validator instance
_validator = DataValidator()

def get_validator() -> DataValidator:
    """Get global validator instance."""
    return _validator

