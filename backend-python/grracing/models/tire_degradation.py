"""
Production Tire Degradation Model

Fits degradation curves and predicts tire performance drop-off.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy.optimize import curve_fit
import warnings
warnings.filterwarnings('ignore')


class TireDegradationModel:
    """
    Production tire degradation model.
    
    Fits exponential or polynomial curves to tire degradation data.
    Detects tire cliff (sudden drop-off).
    Predicts drop-off rate.
    """
    
    def __init__(self):
        self.degradation_curves = {}  # Cache fitted curves per compound
        
    def fit_degradation_curve(
        self,
        lap_times: List[float],
        tire_ages: List[int],
        compound: str = "MEDIUM"
    ) -> Dict:
        """
        Fit degradation curve to data.
        
        Args:
            lap_times: Lap times in seconds
            tire_ages: Corresponding tire ages (lap numbers)
            compound: Tire compound
            
        Returns:
            Fitted degradation parameters
        """
        if len(lap_times) < 3 or len(tire_ages) < 3:
            return self._default_degradation(compound)
        
        lap_times = np.array(lap_times)
        tire_ages = np.array(tire_ages)
        
        # Normalize lap times (base = first few laps average)
        base_pace = np.mean(lap_times[:min(3, len(lap_times))])
        normalized_times = lap_times / base_pace
        
        try:
            # Try exponential fit: pace = 1 + rate * age^exponent
            def exp_curve(age, rate, exponent):
                return 1.0 + rate * (age ** exponent)
            
            popt, _ = curve_fit(
                exp_curve,
                tire_ages,
                normalized_times,
                bounds=([0.0, 0.5], [0.02, 2.0]),  # Reasonable bounds
                maxfev=5000
            )
            
            rate, exponent = popt
            
            # Calculate R²
            predicted = exp_curve(tire_ages, rate, exponent)
            ss_res = np.sum((normalized_times - predicted) ** 2)
            ss_tot = np.sum((normalized_times - np.mean(normalized_times)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
            
            degradation_params = {
                "type": "exponential",
                "rate": float(rate),
                "exponent": float(exponent),
                "base_pace": float(base_pace),
                "r_squared": float(r_squared),
                "compound": compound,
                "confidence": min(len(lap_times) / 20.0, 1.0)
            }
            
        except Exception as e:
            # Fallback to linear fit
            try:
                coeffs = np.polyfit(tire_ages, normalized_times, 1)
                rate = coeffs[0]
                exponent = 1.0
                
                degradation_params = {
                    "type": "linear",
                    "rate": float(rate),
                    "exponent": 1.0,
                    "base_pace": float(base_pace),
                    "r_squared": 0.7,
                    "compound": compound,
                    "confidence": 0.6
                }
            except:
                degradation_params = self._default_degradation(compound)
        
        # Cache for this compound
        self.degradation_curves[compound] = degradation_params
        
        return degradation_params
    
    def predict_degradation(
        self,
        tire_age: int,
        compound: str = "MEDIUM",
        degradation_params: Optional[Dict] = None
    ) -> Dict:
        """
        Predict degradation at specific tire age.
        
        Returns:
            Degradation factor and pace prediction
        """
        if degradation_params is None:
            degradation_params = self.degradation_curves.get(
                compound,
                self._default_degradation(compound)
            )
        
        rate = degradation_params["rate"]
        exponent = degradation_params["exponent"]
        base_pace = degradation_params.get("base_pace", 95.0)
        
        # Calculate degradation: pace = base * (1 + rate * age^exponent)
        degradation_factor = rate * (tire_age ** exponent)
        predicted_pace = base_pace * (1.0 + degradation_factor)
        
        # Detect tire cliff (sudden drop-off)
        # Cliff occurs when degradation rate accelerates significantly
        if tire_age > 20:
            # Calculate rate of change
            degradation_rate = rate * exponent * (tire_age ** (exponent - 1))
            is_cliff = degradation_rate > 0.003  # Threshold for cliff
        else:
            is_cliff = False
        
        return {
            "tire_age": tire_age,
            "degradation_factor": float(degradation_factor),
            "predicted_pace": float(predicted_pace),
            "is_cliff": is_cliff,
            "cliff_lap": self._predict_cliff_lap(degradation_params),
            "confidence": degradation_params.get("confidence", 0.7)
        }
    
    def _predict_cliff_lap(self, degradation_params: Dict) -> int:
        """
        Predict lap when tire cliff will occur.
        """
        rate = degradation_params["rate"]
        exponent = degradation_params["exponent"]
        
        # Find lap where degradation rate exceeds threshold
        for age in range(1, 50):
            degradation_rate = rate * exponent * (age ** (exponent - 1))
            if degradation_rate > 0.003:  # Cliff threshold
                return age
        
        return 30  # Default if no cliff detected
    
    def _default_degradation(self, compound: str) -> Dict:
        """
        Default degradation parameters per compound.
        """
        compound_rates = {
            "SOFT": 0.003,
            "MEDIUM": 0.002,
            "HARD": 0.0015
        }
        
        return {
            "type": "exponential",
            "rate": compound_rates.get(compound, 0.002),
            "exponent": 1.2,
            "base_pace": 95.0,
            "r_squared": 0.7,
            "compound": compound,
            "confidence": 0.5
        }
    
    def calculate_degradation(
        self,
        tire_age: int,
        compound: str = "MEDIUM",
        track_temp: float = 25.0
    ) -> float:
        """
        Calculate degradation percentage.
        
        Simplified version for quick calculations.
        """
        base_rate = 0.002  # Base degradation rate
        
        # Compound adjustments
        compound_multipliers = {
            "SOFT": 1.5,
            "MEDIUM": 1.0,
            "HARD": 0.7
        }
        rate = base_rate * compound_multipliers.get(compound, 1.0)
        
        # Temperature effect (hotter = more degradation)
        temp_multiplier = 1.0 + ((track_temp - 25) * 0.01)
        rate *= temp_multiplier
        
        # Calculate degradation
        degradation = rate * tire_age
        
        return min(degradation, 0.1)  # Cap at 10%


if __name__ == "__main__":
    # Test degradation model
    model = TireDegradationModel()
    
    # Sample data
    lap_times = [95.0, 95.2, 95.5, 95.9, 96.4, 97.0, 97.8]
    tire_ages = [1, 5, 10, 15, 20, 25, 30]
    
    # Fit curve
    params = model.fit_degradation_curve(lap_times, tire_ages, "MEDIUM")
    print("Fitted parameters:", params)
    
    # Predict at age 20
    prediction = model.predict_degradation(20, "MEDIUM", params)
    print("Prediction at age 20:", prediction)

