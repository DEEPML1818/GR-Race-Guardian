"""
Weather Effects Modeling

Models the impact of weather conditions on race pace, tire degradation, and driver performance.
"""

import numpy as np
from typing import Dict, Optional, Tuple


class WeatherModel:
    """
    Models weather effects on racing performance
    """
    
    def __init__(self):
        # Base pace modifiers
        self.base_pace_modifiers = {
            'dry': 1.0,
            'wet': 1.15,  # 15% slower in wet
            'damp': 1.08,  # 8% slower when damp
            'mixed': 1.12  # Mixed conditions
        }
        
        # Tire degradation modifiers
        self.degradation_modifiers = {
            'dry': 1.0,
            'wet': 0.7,  # Less degradation in wet (cooler)
            'damp': 0.85,
            'mixed': 0.9
        }
        
        # Temperature effect coefficients
        self.temp_effect_per_deg = 0.002  # 0.2% per degree C
        
    def determine_condition(self, track_temp: float, ambient_temp: float, 
                           humidity: float, rainfall: float) -> str:
        """
        Determine track condition based on weather variables
        
        Args:
            track_temp: Track temperature in Celsius
            ambient_temp: Ambient temperature in Celsius
            humidity: Humidity percentage (0-100)
            rainfall: Rainfall rate (mm/h)
            
        Returns:
            Condition string: 'dry', 'damp', 'wet', 'mixed'
        """
        if rainfall > 0.5:
            return 'wet'
        elif rainfall > 0.1 or humidity > 80:
            return 'damp'
        elif track_temp < 15 or track_temp > 50:
            return 'mixed'  # Extreme temps can affect grip
        else:
            return 'dry'
    
    def calculate_pace_modifier(self, track_temp: float, ambient_temp: float,
                               humidity: float, rainfall: float) -> float:
        """
        Calculate pace modifier based on weather conditions
        
        Returns:
            Multiplier for lap time (1.0 = no effect, >1.0 = slower)
        """
        condition = self.determine_condition(track_temp, ambient_temp, humidity, rainfall)
        base_modifier = self.base_pace_modifiers.get(condition, 1.0)
        
        # Temperature effect (optimal around 25-30°C)
        optimal_temp = 27.5
        temp_delta = abs(track_temp - optimal_temp)
        temp_modifier = 1.0 + (temp_delta * self.temp_effect_per_deg)
        
        # Combine effects
        total_modifier = base_modifier * temp_modifier
        
        return total_modifier
    
    def calculate_degradation_modifier(self, track_temp: float, ambient_temp: float,
                                      humidity: float, rainfall: float) -> float:
        """
        Calculate tire degradation modifier
        
        Returns:
            Multiplier for degradation rate (1.0 = normal, <1.0 = less degradation)
        """
        condition = self.determine_condition(track_temp, ambient_temp, humidity, rainfall)
        base_modifier = self.degradation_modifiers.get(condition, 1.0)
        
        # Temperature effect on degradation
        # Higher temps = more degradation
        temp_effect = 1.0 + ((track_temp - 25) * 0.01)  # 1% per degree above 25°C
        temp_effect = max(0.5, min(2.0, temp_effect))  # Clamp between 0.5 and 2.0
        
        total_modifier = base_modifier * temp_effect
        
        return total_modifier
    
    def adjust_lap_time(self, base_lap_time: float, track_temp: float,
                       ambient_temp: float, humidity: float, rainfall: float) -> float:
        """
        Adjust lap time based on weather conditions
        
        Args:
            base_lap_time: Base lap time in seconds
            track_temp: Track temperature in Celsius
            ambient_temp: Ambient temperature in Celsius
            humidity: Humidity percentage
            rainfall: Rainfall rate (mm/h)
            
        Returns:
            Adjusted lap time in seconds
        """
        modifier = self.calculate_pace_modifier(track_temp, ambient_temp, humidity, rainfall)
        return base_lap_time * modifier
    
    def adjust_degradation_rate(self, base_rate: float, track_temp: float,
                               ambient_temp: float, humidity: float, rainfall: float) -> float:
        """
        Adjust tire degradation rate based on weather
        
        Args:
            base_rate: Base degradation rate per lap
            track_temp: Track temperature in Celsius
            ambient_temp: Ambient temperature in Celsius
            humidity: Humidity percentage
            rainfall: Rainfall rate (mm/h)
            
        Returns:
            Adjusted degradation rate
        """
        modifier = self.calculate_degradation_modifier(track_temp, ambient_temp, humidity, rainfall)
        return base_rate * modifier
    
    def predict_weather_evolution(self, current_weather: Dict, laps_ahead: int = 10) -> Dict:
        """
        Predict weather conditions N laps ahead (simplified model)
        
        Args:
            current_weather: Dictionary with current weather data
            laps_ahead: Number of laps to predict ahead
            
        Returns:
            Predicted weather conditions
        """
        # Simplified prediction - assumes gradual change
        track_temp = current_weather.get('track_temp', 25)
        rainfall = current_weather.get('rainfall', 0)
        
        # Assume track temp decreases by 0.1°C per lap (cooling)
        predicted_temp = max(15, track_temp - (laps_ahead * 0.1))
        
        # Assume rainfall decreases by 0.05mm/h per lap
        predicted_rainfall = max(0, rainfall - (laps_ahead * 0.05))
        
        return {
            'track_temp': predicted_temp,
            'ambient_temp': current_weather.get('ambient_temp', 25) - (laps_ahead * 0.05),
            'humidity': current_weather.get('humidity', 50),
            'rainfall': predicted_rainfall,
            'condition': self.determine_condition(
                predicted_temp,
                current_weather.get('ambient_temp', 25) - (laps_ahead * 0.05),
                current_weather.get('humidity', 50),
                predicted_rainfall
            )
        }


def load_weather_from_csv(csv_path: str, race_lap: int = 1) -> Optional[Dict]:
    """
    Load weather data from CSV file (compatible with GR Cup format)
    
    Args:
        csv_path: Path to weather CSV file
        race_lap: Lap number to get weather for
        
    Returns:
        Dictionary with weather data or None if not found
    """
    try:
        import pandas as pd
        df = pd.read_csv(csv_path)
        
        # Find weather data for the specified lap
        # Adjust column names based on actual CSV format
        if len(df) > 0:
            row = df.iloc[min(race_lap - 1, len(df) - 1)]
            
            # Map common column names
            weather_data = {
                'track_temp': row.get('Track Temperature', row.get('TrackTemp', 25)),
                'ambient_temp': row.get('Ambient Temperature', row.get('AmbientTemp', 25)),
                'humidity': row.get('Humidity', row.get('RH', 50)),
                'rainfall': row.get('Rainfall', row.get('Rain', 0))
            }
            
            return weather_data
    except Exception as e:
        print(f"Error loading weather data: {e}")
        return None
    
    return None

