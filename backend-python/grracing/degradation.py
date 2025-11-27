"""
Tire Degradation Modeling - Professional motorsport tire wear curves.

Implements industry-standard degradation modeling using:
- Exponential decay curves
- Linear degradation with temperature effects
- Compound-specific models
- Regression-to-track-temperature
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from scipy.optimize import curve_fit
from scipy.stats import linregress


class TireDegradationModel:
    """
    Professional tire degradation modeling for race strategy.
    
    Models tire performance dropoff over laps using:
    - Exponential decay (primary model)
    - Linear degradation (simplified)
    - Compound-specific coefficients
    - Temperature effects
    """
    
    def __init__(self, compound: str = "SOFT", track_temp: float = 25.0):
        """
        Initialize degradation model.
        
        Args:
            compound: Tire compound (SOFT, MEDIUM, HARD, etc.)
            track_temp: Track temperature in Celsius
        """
        self.compound = compound
        self.track_temp = track_temp
        
        # Base degradation coefficients by compound (seconds per lap per lap)
        self.compound_coefficients = {
            "SOFT": 0.08,  # 0.08s degradation per lap
            "MEDIUM": 0.05,
            "HARD": 0.03,
            "SUPER_SOFT": 0.10,
            "INTERMEDIATE": 0.12,
            "WET": 0.15
        }
        
        # Temperature effect coefficient
        self.temp_coefficient = 0.002  # 0.002s per degree Celsius above optimal
        
        # Optimal temperature range (Celsius)
        self.optimal_temp_range = {
            "SOFT": (30, 40),
            "MEDIUM": (35, 45),
            "HARD": (40, 50)
        }
    
    def exponential_degradation(self, lap_number: int, base_time: float, 
                               degradation_rate: Optional[float] = None) -> float:
        """
        Exponential degradation model: time = base * (1 + rate)^lap
        
        Args:
            lap_number: Current lap number (0-indexed)
            base_time: Base lap time in seconds
            degradation_rate: Optional override for degradation rate
        
        Returns:
            Predicted lap time in seconds
        """
        if degradation_rate is None:
            degradation_rate = self.compound_coefficients.get(self.compound, 0.05)
        
        # Exponential model: time increases exponentially with lap count
        degradation_factor = (1 + degradation_rate) ** lap_number
        return base_time * degradation_factor
    
    def linear_degradation(self, lap_number: int, base_time: float,
                          degradation_per_lap: Optional[float] = None) -> float:
        """
        Linear degradation model: time = base + (degradation * lap)
        
        Args:
            lap_number: Current lap number (0-indexed)
            base_time: Base lap time in seconds
            degradation_per_lap: Optional override for degradation per lap
        
        Returns:
            Predicted lap time in seconds
        """
        if degradation_per_lap is None:
            degradation_per_lap = self.compound_coefficients.get(self.compound, 0.05) * base_time
        
        return base_time + (degradation_per_lap * lap_number)
    
    def temperature_adjusted_degradation(self, lap_number: int, base_time: float,
                                        current_temp: Optional[float] = None) -> float:
        """
        Degradation model with temperature effects.
        
        Higher temperatures accelerate degradation.
        """
        if current_temp is None:
            current_temp = self.track_temp
        
        # Base degradation
        base_degradation = self.linear_degradation(lap_number, base_time)
        
        # Temperature adjustment
        optimal_range = self.optimal_temp_range.get(self.compound, (30, 40))
        optimal_temp = (optimal_range[0] + optimal_range[1]) / 2
        
        temp_delta = current_temp - optimal_temp
        temp_adjustment = base_degradation * (1 + abs(temp_delta) * self.temp_coefficient)
        
        # If too hot or too cold, degradation increases
        if temp_delta > 5 or temp_delta < -5:
            temp_adjustment *= 1.2
        
        return temp_adjustment
    
    def fit_degradation_curve(self, lap_times: List[float], 
                             lap_numbers: Optional[List[int]] = None) -> Dict:
        """
        Fit degradation curve to actual lap time data.
        
        Uses scipy curve fitting to determine degradation parameters.
        
        Returns:
            Dict with fitted parameters and model type
        """
        if lap_numbers is None:
            lap_numbers = list(range(len(lap_times)))
        
        if len(lap_times) < 3:
            return {'error': 'Insufficient data points'}
        
        lap_nums = np.array(lap_numbers)
        times = np.array(lap_times)
        
        # Try linear fit first
        try:
            slope, intercept, r_value, p_value, std_err = linregress(lap_nums, times)
            
            linear_r_squared = r_value ** 2
            
            # Try exponential fit: time = a * (1 + b)^lap
            def exp_model(x, a, b):
                return a * ((1 + b) ** x)
            
            try:
                popt, pcov = curve_fit(exp_model, lap_nums, times, 
                                     p0=[times[0], 0.01], maxfexp=10000)
                exp_params = popt
                exp_times = exp_model(lap_nums, *exp_params)
                exp_r_squared = 1 - np.sum((times - exp_times) ** 2) / np.sum((times - np.mean(times)) ** 2)
            except:
                exp_r_squared = 0
                exp_params = [times[0], 0.01]
            
            # Choose best model
            if exp_r_squared > linear_r_squared:
                model_type = 'exponential'
                degradation_rate = exp_params[1]
                base_time = exp_params[0]
            else:
                model_type = 'linear'
                degradation_rate = slope
                base_time = intercept
            
            return {
                'model_type': model_type,
                'degradation_rate': degradation_rate,
                'base_time': base_time,
                'r_squared': max(linear_r_squared, exp_r_squared),
                'linear_r_squared': linear_r_squared,
                'exponential_r_squared': exp_r_squared if 'exp_r_squared' in locals() else 0
            }
        except Exception as e:
            return {'error': str(e)}
    
    def predict_stint_degradation(self, base_time: float, stint_length: int,
                                 model_type: str = 'linear') -> List[float]:
        """
        Predict lap times for entire stint.
        
        Args:
            base_time: Starting lap time in seconds
            stint_length: Number of laps in stint
            model_type: 'linear' or 'exponential'
        
        Returns:
            List of predicted lap times
        """
        predicted_times = []
        
        for lap in range(stint_length):
            if model_type == 'exponential':
                time = self.exponential_degradation(lap, base_time)
            else:
                time = self.linear_degradation(lap, base_time)
            
            predicted_times.append(time)
        
        return predicted_times
    
    def calculate_pit_window(self, current_time: float, degradation_rate: float,
                           pit_loss: float = 25.0) -> Dict:
        """
        Calculate optimal pit window based on degradation.
        
        Pit when: (time_saved_by_new_tires) > (pit_loss)
        
        Args:
            current_time: Current lap time
            degradation_rate: Current degradation rate
            pit_loss: Time lost in pit (seconds)
        
        Returns:
            Dict with pit window analysis
        """
        # Estimate when degradation makes pit stop worthwhile
        # New tires = base_time (fresher)
        # Current tires continue degrading
        
        base_time = current_time / (1 + degradation_rate)
        
        # Find lap where pit stop becomes beneficial
        optimal_pit_lap = None
        for lap in range(1, 100):
            degraded_time = self.linear_degradation(lap, base_time, 
                                                   degradation_rate * base_time)
            new_tire_time = base_time
            time_gain = degraded_time - new_tire_time
            
            if time_gain > pit_loss:
                optimal_pit_lap = lap
                break
        
        return {
            'optimal_pit_lap': optimal_pit_lap,
            'current_time': current_time,
            'fresher_time': base_time,
            'time_gain_per_lap': degradation_rate * base_time,
            'pit_loss': pit_loss
        }


class FuelEffectModel:
    """
    Fuel load effect modeling.
    
    Typically: ~0.03 seconds per 10kg of fuel burned
    """
    
    def __init__(self, fuel_consumption_per_lap: float = 2.0,  # kg per lap
                 fuel_effect_per_10kg: float = 0.03):  # seconds per 10kg
        self.fuel_consumption_per_lap = fuel_consumption_per_lap
        self.fuel_effect_per_10kg = fuel_effect_per_10kg
    
    def calculate_fuel_effect(self, lap_number: int, starting_fuel: float = 100.0) -> float:
        """
        Calculate lap time effect due to fuel weight.
        
        Args:
            lap_number: Current lap number (0-indexed)
            starting_fuel: Starting fuel load in kg
        
        Returns:
            Time improvement due to fuel burn (negative = faster)
        """
        remaining_fuel = starting_fuel - (lap_number * self.fuel_consumption_per_lap)
        fuel_burned = starting_fuel - remaining_fuel
        
        # Fuel weight improves lap time (less weight = faster)
        time_improvement = -(fuel_burned / 10.0) * self.fuel_effect_per_10kg
        
        return time_improvement


def fit_degradation_from_data(df: pd.DataFrame, driver_id: Optional[str] = None) -> Dict:
    """
    Convenience function to fit degradation model from lap data.
    
    Args:
        df: DataFrame with lap times
        driver_id: Optional driver ID to filter
    
    Returns:
        Fitted degradation model parameters
    """
    if driver_id and 'vehicle_id' in df.columns:
        driver_df = df[df['vehicle_id'] == driver_id]
    else:
        driver_df = df
    
    # Get lap times
    lap_time_cols = ['lap_time', 'LapTime', 'LAP_TIME', 'lap_time_seconds']
    lap_time_col = None
    for col in lap_time_cols:
        if col in driver_df.columns:
            lap_time_col = col
            break
    
    if not lap_time_col:
        return {'error': 'No lap time column found'}
    
    # Convert to seconds and extract
    times = []
    laps = []
    for idx, row in driver_df.iterrows():
        t = row[lap_time_col]
        if pd.notna(t):
            if isinstance(t, (int, float)):
                times.append(float(t))
            else:
                parts = str(t).split(':')
                if len(parts) == 2:
                    times.append(float(parts[0]) * 60 + float(parts[1]))
                else:
                    try:
                        times.append(float(t))
                    except:
                        continue
            
            if 'lap' in driver_df.columns:
                laps.append(int(row['lap']))
            else:
                laps.append(len(times) - 1)
    
    if len(times) < 3:
        return {'error': 'Insufficient data points'}
    
    model = TireDegradationModel()
    return model.fit_degradation_curve(times, laps)

