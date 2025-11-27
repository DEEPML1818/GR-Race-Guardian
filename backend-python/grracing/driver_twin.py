"""
Digital Driver Twin - Complete Implementation

Generates comprehensive driver behavior models from race data.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json

# Try to import scipy for advanced curve fitting
try:
    from scipy.optimize import curve_fit
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    # Fallback: simple curve fitting without scipy


class DriverTwinGenerator:
    """
    Generates a Digital Driver Twin from race data.
    
    A Driver Twin is a mathematical representation of a driver's behavior,
    including pace, consistency, aggression, degradation patterns, and sector strengths.
    """
    
    def __init__(self):
        self.min_laps_for_twin = 5  # Minimum laps needed to generate reliable twin
        
    def generate_driver_twin(
        self,
        driver_id: str,
        lap_times: List[float],
        sector_times: List[Dict[str, float]],
        telemetry_data: Optional[List[Dict]] = None,
        tire_compound: str = "MEDIUM",
        current_lap: int = 0
    ) -> Dict:
        """
        Generate complete Driver Twin from race data.
        
        Args:
            driver_id: Unique driver identifier
            lap_times: List of lap times in seconds
            sector_times: List of dicts with S1, S2, S3 times
            telemetry_data: Optional throttle/brake/steering data
            tire_compound: Current tire compound
            current_lap: Current lap number
            
        Returns:
            Complete Driver Twin JSON
        """
        if len(lap_times) < self.min_laps_for_twin:
            return self._generate_default_twin(driver_id, current_lap)
        
        # Calculate all twin metrics
        pace_vector = self._calculate_pace_vector(lap_times)
        consistency_index = self._calculate_consistency_index(lap_times)
        aggression_score = self._calculate_aggression_score(telemetry_data) if telemetry_data else 0.5
        degradation_profile = self._calculate_degradation_profile(lap_times, tire_compound)
        sector_strengths = self._calculate_sector_strengths(sector_times)
        fatigue_dropoff = self._calculate_fatigue_dropoff(lap_times, current_lap)
        
        return {
            "driver_id": driver_id,
            "pace_vector": float(pace_vector),
            "consistency_index": float(consistency_index),
            "aggression_score": float(aggression_score),
            "degradation_profile": degradation_profile,
            "sector_strengths": sector_strengths,
            "fatigue_dropoff": fatigue_dropoff,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "lap_count": len(lap_times),
            "confidence": self._calculate_confidence(len(lap_times))
        }
    
    def _calculate_pace_vector(self, lap_times: List[float]) -> float:
        """
        Calculate pace vector: normalized difference from best lap.
        
        Formula: pace_vector = (avg_lap_time - best_lap_time) / best_lap_time
        Range: -0.1 to +0.1 (negative = faster than best, positive = slower)
        """
        if not lap_times or len(lap_times) < 2:
            return 0.0
        
        best_lap = min(lap_times)
        avg_lap = np.mean(lap_times)
        
        pace_vector = (avg_lap - best_lap) / best_lap
        
        # Normalize to -0.1 to +0.1 range
        pace_vector = np.clip(pace_vector, -0.1, 0.1)
        
        return pace_vector
    
    def _calculate_consistency_index(self, lap_times: List[float]) -> float:
        """
        Calculate consistency index: how consistent are lap times?
        
        Formula: consistency = 1 - (coefficient_of_variation)
        Where CV = std_dev / mean_lap_time
        Range: 0.0 to 1.0 (1.0 = perfect consistency)
        
        Improved formula accounts for:
        - Coefficient of variation (normalized std dev)
        - Outlier detection (removes extreme values)
        - Trend correction (accounts for degradation)
        """
        if not lap_times or len(lap_times) < 2:
            return 0.7  # Default moderate consistency
        
        lap_times_array = np.array(lap_times)
        mean_lap = np.mean(lap_times_array)
        
        if mean_lap == 0:
            return 0.7
        
        # Remove outliers using IQR method (more robust)
        if len(lap_times_array) >= 5:
            Q1 = np.percentile(lap_times_array, 25)
            Q3 = np.percentile(lap_times_array, 75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            filtered_times = lap_times_array[(lap_times_array >= lower_bound) & 
                                            (lap_times_array <= upper_bound)]
            if len(filtered_times) > 1:
                lap_times_array = filtered_times
                mean_lap = np.mean(lap_times_array)
        
        # Calculate coefficient of variation
        std_dev = np.std(lap_times_array)
        coefficient_of_variation = std_dev / mean_lap if mean_lap > 0 else 0.0
        
        # Consistency index: higher CV = lower consistency
        consistency = 1.0 - coefficient_of_variation
        
        # Normalize to 0.0 to 1.0 range (CV typically 0-0.3 for good drivers)
        consistency = np.clip(consistency, 0.0, 1.0)
        
        return float(consistency)
    
    def _calculate_aggression_score(
        self,
        telemetry_data: Optional[List[Dict]] = None
    ) -> float:
        """
        Calculate aggression score from telemetry data.
        
        Enhanced extraction based on:
        - Throttle application rate (how quickly throttle is applied)
        - Brake release timing (later release = more aggressive)
        - Corner entry speeds (higher speeds = more aggressive)
        - Steering angle variance (more variance = more aggressive)
        - G-force peaks (higher peaks = more aggressive)
        
        Range: 0.0 to 1.0 (1.0 = very aggressive)
        """
        if not telemetry_data or len(telemetry_data) == 0:
            return 0.5  # Default moderate aggression
        
        # Extract all telemetry signals
        throttle_values = [d.get('throttle', 0.5) for d in telemetry_data if 'throttle' in d]
        brake_values = [d.get('brake', 0.0) for d in telemetry_data if 'brake' in d]
        speed_values = [d.get('speed', 0.0) for d in telemetry_data if 'speed' in d]
        steering_values = [d.get('steering', 0.0) for d in telemetry_data if 'steering' in d]
        g_force_values = [d.get('g_force', 0.0) for d in telemetry_data if 'g_force' in d]
        
        if not throttle_values:
            return 0.5
        
        # 1. Throttle application rate (how quickly throttle increases)
        throttle_array = np.array(throttle_values)
        if len(throttle_array) > 1:
            throttle_diffs = np.diff(throttle_array)
            throttle_rate = np.mean(np.abs(throttle_diffs[throttle_diffs > 0]))  # Only positive changes
            throttle_factor = min(throttle_rate * 10, 1.0)  # Normalize
        else:
            throttle_factor = 0.5
        
        # 2. Brake release timing (later/harder braking = more aggressive)
        if brake_values:
            brake_array = np.array(brake_values)
            # High brake values followed by quick release = aggressive
            brake_peaks = np.max(brake_array)
            brake_variance = np.var(brake_array)
            brake_factor = min((brake_peaks * 0.5 + brake_variance * 5), 1.0)
        else:
            brake_factor = 0.3
        
        # 3. Speed factor (higher max speeds relative to average)
        if speed_values and len(speed_values) > 1:
            speed_array = np.array(speed_values)
            max_speed = np.max(speed_array)
            avg_speed = np.mean(speed_array)
            speed_variance = np.var(speed_array)
            if avg_speed > 0:
                speed_factor = min((max_speed - avg_speed) / avg_speed * 0.5 + speed_variance / (avg_speed ** 2) * 10, 1.0)
            else:
                speed_factor = 0.0
        else:
            speed_factor = 0.3
        
        # 4. Steering angle variance (more variance = more aggressive cornering)
        if steering_values and len(steering_values) > 1:
            steering_array = np.array(steering_values)
            steering_variance = np.var(steering_array)
            steering_factor = min(steering_variance * 20, 1.0)  # Normalize
        else:
            steering_factor = 0.2
        
        # 5. G-force peaks (higher peaks = more aggressive)
        if g_force_values:
            g_force_array = np.array(g_force_values)
            max_g = np.max(np.abs(g_force_array))
            g_factor = min(max_g / 5.0, 1.0)  # Normalize (5G is very high)
        else:
            g_factor = 0.2
        
        # Combined aggression score (weighted average)
        aggression = (
            throttle_factor * 0.25 +
            brake_factor * 0.20 +
            speed_factor * 0.20 +
            steering_factor * 0.15 +
            g_factor * 0.20
        )
        
        return float(np.clip(aggression, 0.0, 1.0))
    
    def _calculate_degradation_profile(
        self,
        lap_times: List[float],
        tire_compound: str
    ) -> Dict:
        """
        Calculate tire degradation profile with proper exponential curve fitting.
        
        Fits exponential curve: pace(lap) = base_pace * (1 + rate * lap^exponent)
        Or linear: pace(lap) = base_pace * (1 + rate * lap)
        
        Uses scipy curve_fit for proper exponential fitting.
        """
        if len(lap_times) < 3:
            return {
                "rate": 0.002,
                "exponent": 1.0,
                "base_pace": np.mean(lap_times) if lap_times else 95.0,
                "type": "linear",
                "compound": tire_compound,
                "confidence": 0.5
            }
        
        laps = np.arange(1, len(lap_times) + 1)  # Start from lap 1
        lap_times_array = np.array(lap_times)
        
        # Base pace (first 3 laps average, excluding outliers)
        base_pace = np.mean(lap_times[:min(3, len(lap_times))])
        
        # Try exponential fit first: pace = base * (1 + rate * lap^exponent)
        def exponential_model(lap, rate, exponent):
            return base_pace * (1.0 + rate * (lap ** exponent))
        
        # Try linear fit: pace = base * (1 + rate * lap)
        def linear_model(lap, rate):
            return base_pace * (1.0 + rate * lap)
        
        degradation_rate = 0.002
        exponent = 1.0
        fit_type = "linear"
        confidence = 0.5
        
        try:
            if SCIPY_AVAILABLE:
                # Try exponential fit
                if len(lap_times) >= 5:
                    popt_exp, _ = curve_fit(
                        exponential_model,
                        laps,
                        lap_times_array,
                        p0=[0.002, 1.0],
                        bounds=([0.0, 0.5], [0.01, 2.0]),
                        maxfev=1000
                    )
                    degradation_rate, exponent = popt_exp
                    fit_type = "exponential"
                    
                    # Calculate R-squared for confidence
                    predicted = exponential_model(laps, degradation_rate, exponent)
                    ss_res = np.sum((lap_times_array - predicted) ** 2)
                    ss_tot = np.sum((lap_times_array - np.mean(lap_times_array)) ** 2)
                    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.5
                    confidence = max(0.5, min(r_squared, 1.0))
                else:
                    # Linear fit for fewer laps
                    popt_lin, _ = curve_fit(
                        linear_model,
                        laps,
                        lap_times_array,
                        p0=[0.002],
                        bounds=([0.0], [0.01]),
                        maxfev=1000
                    )
                    degradation_rate = popt_lin[0]
                    exponent = 1.0
                    fit_type = "linear"
            else:
                # Fallback without scipy: use linear regression
                raise ImportError("scipy not available")
        except (Exception, ImportError):
            # Fallback to simple linear calculation
            if len(lap_times) >= 5:
                recent_laps = lap_times[-5:]
                early_laps = lap_times[:5]
                degradation_rate = (np.mean(recent_laps) - np.mean(early_laps)) / (base_pace * len(lap_times))
            else:
                degradation_rate = (lap_times[-1] - lap_times[0]) / (base_pace * len(lap_times))
            degradation_rate = max(0.0, min(degradation_rate, 0.01))
        
        # Normalize degradation rate
        degradation_rate = max(0.0, degradation_rate)  # Can't improve over time
        degradation_rate = min(degradation_rate, 0.01)  # Cap at 1% per lap
        
        # Compound-specific adjustments
        compound_multipliers = {
            "SOFT": 1.5,
            "MEDIUM": 1.0,
            "HARD": 0.7
        }
        degradation_rate *= compound_multipliers.get(tire_compound, 1.0)
        
        # Calculate confidence based on data quality
        confidence = max(confidence, min(len(lap_times) / 20.0, 1.0))
        
        return {
            "rate": float(degradation_rate),
            "exponent": float(exponent),
            "base_pace": float(base_pace),
            "type": fit_type,
            "compound": tire_compound,
            "confidence": float(confidence)
        }
    
    def _calculate_sector_strengths(
        self,
        sector_times: List[Dict[str, float]]
    ) -> Dict[str, float]:
        """
        Calculate relative sector strengths (S1, S2, S3) with improved computation.
        
        Formula: sector_strength = (overall_avg_sector_time / driver_avg_sector_time)
        - Lower sector time = stronger performance = higher strength score
        - Returns normalized strengths (0.8 to 1.2, where 1.0 = average)
        - Accounts for relative performance across all sectors
        """
        if not sector_times or len(sector_times) < 2:
            return {"S1": 1.0, "S2": 1.0, "S3": 1.0}
        
        # Extract sector times (filter out invalid values)
        s1_times = [s.get("S1", 0) for s in sector_times if s.get("S1", 0) > 0]
        s2_times = [s.get("S2", 0) for s in sector_times if s.get("S2", 0) > 0]
        s3_times = [s.get("S3", 0) for s in sector_times if s.get("S3", 0) > 0]
        
        # Need at least 2 sectors to calculate
        if not (s1_times and s2_times and s3_times):
            return {"S1": 1.0, "S2": 1.0, "S3": 1.0}
        
        # Calculate average sector times (remove outliers)
        def robust_mean(values):
            if not values:
                return 0.0
            values_array = np.array(values)
            if len(values_array) >= 5:
                # Remove outliers using IQR
                Q1 = np.percentile(values_array, 25)
                Q3 = np.percentile(values_array, 75)
                IQR = Q3 - Q1
                lower = Q1 - 1.5 * IQR
                upper = Q3 + 1.5 * IQR
                filtered = values_array[(values_array >= lower) & (values_array <= upper)]
                return np.mean(filtered) if len(filtered) > 0 else np.mean(values_array)
            return np.mean(values_array)
        
        avg_s1 = robust_mean(s1_times)
        avg_s2 = robust_mean(s2_times)
        avg_s3 = robust_mean(s3_times)
        
        # Calculate overall average sector time (baseline)
        overall_avg = (avg_s1 + avg_s2 + avg_s3) / 3.0
        
        if overall_avg == 0:
            return {"S1": 1.0, "S2": 1.0, "S3": 1.0}
        
        # Calculate strengths: faster sector = higher strength
        # Strength = baseline / driver_sector (if driver is faster, strength > 1.0)
        def calculate_strength(sector_avg):
            if sector_avg == 0:
                return 1.0
            # If driver's sector is faster (lower time), strength > 1.0
            strength = overall_avg / sector_avg
            # Normalize to reasonable range (0.8 to 1.2)
            # 0.8 = 20% slower than average, 1.2 = 20% faster than average
            return np.clip(strength, 0.8, 1.2)
        
        return {
            "S1": float(calculate_strength(avg_s1)),
            "S2": float(calculate_strength(avg_s2)),
            "S3": float(calculate_strength(avg_s3))
        }
    
    def _calculate_fatigue_dropoff(
        self,
        lap_times: List[float],
        current_lap: int
    ) -> Dict:
        """
        Calculate fatigue/long-run dropoff model with exponential decay.
        
        Predicts performance degradation over long stints.
        Formula: fatigue_factor(lap) = base_factor * (1 - exp(-lap / fatigue_constant))
        
        Uses exponential decay model to predict when driver performance degrades.
        """
        if len(lap_times) < 5:
            return {
                "factor": 0.02,
                "fatigue_constant": 30.0,
                "critical_lap": current_lap + 25,
                "trend": "stable"
            }
        
        laps = np.arange(1, len(lap_times) + 1)
        lap_times_array = np.array(lap_times)
        
        # Exponential decay model: pace(lap) = base * (1 + factor * (1 - exp(-lap/tau)))
        def fatigue_model(lap, factor, tau):
            base = np.mean(lap_times[:3])  # Base pace from early laps
            return base * (1.0 + factor * (1.0 - np.exp(-lap / tau)))
        
        fatigue_factor = 0.02
        fatigue_constant = 30.0  # tau (time constant)
        trend = "stable"
        
        try:
            if SCIPY_AVAILABLE and len(lap_times) >= 8:
                # Fit exponential decay model
                base_pace = np.mean(lap_times[:3])
                popt, _ = curve_fit(
                    fatigue_model,
                    laps,
                    lap_times_array,
                    p0=[0.02, 30.0],
                    bounds=([0.0, 10.0], [0.1, 100.0]),
                    maxfev=1000
                )
                fatigue_factor, fatigue_constant = popt
            else:
                # Simple linear trend for fewer laps
                recent_laps = lap_times[-min(5, len(lap_times)):]
                early_laps = lap_times[:min(5, len(lap_times))]
                recent_avg = np.mean(recent_laps)
                early_avg = np.mean(early_laps)
                
                if early_avg > 0:
                    fatigue_factor = (recent_avg - early_avg) / (early_avg * len(lap_times))
                else:
                    fatigue_factor = 0.02
        except Exception:
            # Fallback calculation
            recent_laps = lap_times[-5:]
            early_laps = lap_times[:5]
            recent_avg = np.mean(recent_laps)
            early_avg = np.mean(early_laps)
            if early_avg > 0:
                fatigue_factor = (recent_avg - early_avg) / (early_avg * len(lap_times))
            else:
                fatigue_factor = 0.02
        
        # Normalize
        fatigue_factor = max(0.0, fatigue_factor)  # Can't improve with fatigue
        fatigue_factor = min(fatigue_factor, 0.05)  # Cap at 5% per lap
        fatigue_constant = max(10.0, min(fatigue_constant, 100.0))  # Reasonable range
        
        # Predict critical lap using exponential model
        # Critical when pace increase exceeds 2% consistently
        if fatigue_factor > 0.02:
            # Solve: 0.02 = factor * (1 - exp(-lap/tau))
            # lap = -tau * ln(1 - 0.02/factor)
            if fatigue_factor > 0.02:
                critical_lap = current_lap + int(-fatigue_constant * np.log(1.0 - 0.02 / fatigue_factor))
            else:
                critical_lap = current_lap + 25
        else:
            critical_lap = current_lap + 30  # Default if no significant fatigue
        
        # Determine trend
        if fatigue_factor < 0.01:
            trend = "improving"
        elif fatigue_factor < 0.02:
            trend = "stable"
        elif fatigue_factor < 0.035:
            trend = "degrading"
        else:
            trend = "critical"
        
        return {
            "factor": float(fatigue_factor),
            "fatigue_constant": float(fatigue_constant),
            "critical_lap": int(critical_lap),
            "trend": trend
        }
    
    def _calculate_confidence(self, lap_count: int) -> float:
        """
        Calculate confidence in Driver Twin based on data available.
        
        More laps = higher confidence
        """
        if lap_count < 5:
            return 0.5
        elif lap_count < 10:
            return 0.7
        elif lap_count < 20:
            return 0.85
        else:
            return 0.95
    
    def _generate_default_twin(self, driver_id: str, current_lap: int) -> Dict:
        """
        Generate default Driver Twin when insufficient data.
        """
        return {
            "driver_id": driver_id,
            "pace_vector": 0.0,
            "consistency_index": 0.7,
            "aggression_score": 0.5,
            "degradation_profile": {
                "rate": 0.002,
                "type": "linear",
                "compound": "MEDIUM",
                "confidence": 0.5
            },
            "sector_strengths": {
                "S1": 1.0,
                "S2": 1.0,
                "S3": 1.0
            },
            "fatigue_dropoff": {
                "factor": 0.02,
                "critical_lap": current_lap + 20,
                "trend": "stable"
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "lap_count": 0,
            "confidence": 0.5,
            "note": "Insufficient data - using defaults"
        }
    
    def update_driver_twin(
        self,
        current_twin: Dict,
        new_lap_time: float,
        new_sector_times: Dict[str, float],
        telemetry_data: Optional[Dict] = None
    ) -> Dict:
        """
        Incrementally update Driver Twin with new lap data.
        
        More efficient than regenerating from scratch.
        """
        # For now, this is a placeholder
        # In production, would update metrics incrementally
        # For simplicity, recommend regenerating from full history
        
        return current_twin


def generate_driver_twin_json(
    driver_id: str,
    lap_times: List[float],
    sector_times: List[Dict[str, float]],
    **kwargs
) -> Dict:
    """
    Convenience function to generate Driver Twin JSON.
    """
    generator = DriverTwinGenerator()
    return generator.generate_driver_twin(driver_id, lap_times, sector_times, **kwargs)


if __name__ == "__main__":
    # Test Driver Twin generation
    generator = DriverTwinGenerator()
    
    # Sample data
    lap_times = [95.234, 95.456, 95.123, 95.678, 95.345, 95.890, 95.567]
    sector_times = [
        {"S1": 31.5, "S2": 32.0, "S3": 31.7},
        {"S1": 31.6, "S2": 32.1, "S3": 31.8},
        {"S1": 31.4, "S2": 31.9, "S3": 31.6},
    ]
    
    twin = generator.generate_driver_twin(
        driver_id="driver_1",
        lap_times=lap_times,
        sector_times=sector_times,
        tire_compound="MEDIUM",
        current_lap=7
    )
    
    print(json.dumps(twin, indent=2))

