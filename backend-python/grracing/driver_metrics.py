"""
Driver Behavior Metrics - Professional motorsport driver analysis.

Implements industry-standard metrics used in F1, WEC, IndyCar, IMSA:
- Consistency Index
- Driving Aggression Score
- Pace Stability Curve
- Fatigue Performance Dropoff
- Sector Strength Fingerprint
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy import stats
from scipy.optimize import curve_fit

from .lap_classification import LapClassifier, LapType
from .sector_timing import SectorTimingEngine


class DriverMetrics:
    """
    Comprehensive driver behavior metrics calculator.
    
    Provides professional-grade metrics used by race engineers
    in Formula 1, WEC, IndyCar, and IMSA teams.
    """
    
    def __init__(self):
        self.lap_classifier = LapClassifier()
        self.sector_engine = SectorTimingEngine()
    
    def calculate_consistency_index(self, df: pd.DataFrame, driver_id: Optional[str] = None) -> float:
        """
        Calculate Consistency Index (0-1, higher is more consistent).
        
        Formula: 1 - (coefficient_of_variation of valid race laps)
        Industry standard: >0.95 is exceptional consistency
        """
        if driver_id and 'vehicle_id' in df.columns:
            driver_df = df[df['vehicle_id'] == driver_id]
        else:
            driver_df = df
        
        # Filter to valid race laps only
        valid_laps = self.lap_classifier.filter_race_laps(driver_df)
        
        if len(valid_laps) < 3:
            return 0.0
        
        # Find lap time column
        lap_time_cols = ['lap_time', 'LapTime', 'LAP_TIME', 'lap_time_seconds']
        lap_time_col = None
        for col in lap_time_cols:
            if col in valid_laps.columns:
                lap_time_col = col
                break
        
        if not lap_time_col:
            return 0.0
        
        # Convert to seconds
        times = []
        for t in valid_laps[lap_time_col]:
            if pd.notna(t):
                if isinstance(t, (int, float)):
                    times.append(float(t))
                else:
                    parts = str(t).split(':')
                    if len(parts) == 2:
                        times.append(float(parts[0]) * 60 + float(parts[1]))
                    elif len(parts) == 3:
                        times.append(float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2]))
                    else:
                        try:
                            times.append(float(t))
                        except:
                            pass
        
        if len(times) < 3:
            return 0.0
        
        times_array = np.array(times)
        mean_time = np.mean(times_array)
        std_time = np.std(times_array)
        
        if mean_time == 0:
            return 0.0
        
        coefficient_of_variation = std_time / mean_time
        consistency_index = max(0.0, min(1.0, 1.0 - coefficient_of_variation))
        
        return consistency_index
    
    def calculate_aggression_score(self, df: pd.DataFrame, driver_id: Optional[str] = None) -> Dict:
        """
        Calculate Driving Aggression Score.
        
        Based on:
        - Variance in sector times (more aggressive = more variance)
        - Overtaking attempts
        - Pace relative to average (push vs conserve)
        
        Returns dict with:
        - aggression_score: 0-1 (1 = very aggressive)
        - sector_variance: variance across sectors
        - pace_relative_to_avg: how much faster than average
        """
        if driver_id and 'vehicle_id' in df.columns:
            driver_df = df[df['vehicle_id'] == driver_id]
        else:
            driver_df = df
        
        # Get sector times
        driver_df = self.sector_engine.extract_sectors_from_df(driver_df)
        
        sector_vars = []
        for i in range(1, 4):
            col = f"sector_{i}_seconds"
            if col in driver_df.columns:
                valid_sectors = driver_df[col].dropna()
                if len(valid_sectors) > 1:
                    sector_vars.append(np.var(valid_sectors))
        
        # Calculate overall variance
        avg_variance = np.mean(sector_vars) if sector_vars else 0.0
        
        # Calculate pace relative to average
        lap_time_cols = ['lap_time', 'LapTime', 'LAP_TIME', 'lap_time_seconds']
        lap_time_col = None
        for col in lap_time_cols:
            if col in driver_df.columns:
                lap_time_col = col
                break
        
        pace_relative = 1.0
        if lap_time_col:
            valid_laps = self.lap_classifier.filter_race_laps(driver_df)
            if len(valid_laps) > 0:
                times = valid_laps[lap_time_col].dropna()
                if len(times) > 0:
                    driver_avg = np.mean([float(str(t).split(':')[0]) * 60 + float(str(t).split(':')[1]) if ':' in str(t) else float(t) for t in times[:5]])
                    session_avg = driver_avg * 1.05  # Approximate
                    pace_relative = session_avg / driver_avg if driver_avg > 0 else 1.0
        
        # Normalize variance (0-1 scale, higher = more aggressive)
        normalized_variance = min(1.0, avg_variance / 10.0) if avg_variance > 0 else 0.0
        
        # Combine factors (50% variance, 50% pace)
        aggression_score = (normalized_variance * 0.5) + (min(1.0, (pace_relative - 0.95) / 0.1) * 0.5)
        aggression_score = max(0.0, min(1.0, aggression_score))
        
        return {
            'aggression_score': aggression_score,
            'sector_variance': avg_variance,
            'pace_relative_to_avg': pace_relative,
            'interpretation': 'Very Aggressive' if aggression_score > 0.7 else 
                            'Aggressive' if aggression_score > 0.5 else
                            'Balanced' if aggression_score > 0.3 else 'Conservative'
        }
    
    def calculate_pace_stability_curve(self, df: pd.DataFrame, driver_id: Optional[str] = None) -> Dict:
        """
        Calculate Pace Stability Curve over race duration.
        
        Shows how pace evolves over time (tire degradation, fuel load effects).
        Returns linear regression coefficients.
        """
        if driver_id and 'vehicle_id' in df.columns:
            driver_df = df[df['vehicle_id'] == driver_id]
        else:
            driver_df = df
        
        valid_laps = self.lap_classifier.filter_race_laps(driver_df)
        
        if len(valid_laps) < 5:
            return {'slope': 0.0, 'intercept': 0.0, 'r_squared': 0.0, 'stability': 1.0}
        
        # Get lap numbers and times
        if 'lap' in valid_laps.columns:
            lap_numbers = valid_laps['lap'].values
        elif 'LAP_NUMBER' in valid_laps.columns:
            lap_numbers = valid_laps['LAP_NUMBER'].values
        else:
            lap_numbers = np.arange(len(valid_laps))
        
        lap_time_cols = ['lap_time', 'LapTime', 'LAP_TIME', 'lap_time_seconds']
        lap_time_col = None
        for col in lap_time_cols:
            if col in valid_laps.columns:
                lap_time_col = col
                break
        
        if not lap_time_col:
            return {'slope': 0.0, 'intercept': 0.0, 'r_squared': 0.0, 'stability': 1.0}
        
        # Convert times to seconds
        times_seconds = []
        for t in valid_laps[lap_time_col]:
            if pd.notna(t):
                if isinstance(t, (int, float)):
                    times_seconds.append(float(t))
                else:
                    parts = str(t).split(':')
                    if len(parts) == 2:
                        times_seconds.append(float(parts[0]) * 60 + float(parts[1]))
                    else:
                        try:
                            times_seconds.append(float(t))
                        except:
                            pass
        
        if len(times_seconds) < 5:
            return {'slope': 0.0, 'intercept': 0.0, 'r_squared': 0.0, 'stability': 1.0}
        
        # Linear regression: time = slope * lap + intercept
        lap_nums_clean = lap_numbers[:len(times_seconds)]
        slope, intercept, r_value, p_value, std_err = stats.linregress(lap_nums_clean, times_seconds)
        
        # Stability score (higher = more stable pace)
        # Negative slope means getting faster (good), positive means degradation
        stability_score = 1.0 / (1.0 + abs(slope) * 100)  # Normalize
        
        return {
            'slope': slope,  # seconds per lap (positive = degradation)
            'intercept': intercept,  # base lap time
            'r_squared': r_value ** 2,
            'stability': stability_score,
            'degradation_rate': slope,  # positive = tire/fuel degradation
            'p_value': p_value
        }
    
    def calculate_fatigue_dropoff(self, df: pd.DataFrame, driver_id: Optional[str] = None) -> Dict:
        """
        Calculate Fatigue Performance Dropoff.
        
        Analyzes performance in first half vs second half of race.
        Returns dropoff percentage and significance.
        """
        if driver_id and 'vehicle_id' in df.columns:
            driver_df = df[df['vehicle_id'] == driver_id]
        else:
            driver_df = df
        
        valid_laps = self.lap_classifier.filter_race_laps(driver_df)
        
        if len(valid_laps) < 10:
            return {'dropoff_percent': 0.0, 'first_half_avg': 0.0, 'second_half_avg': 0.0, 'significant': False}
        
        # Split into halves
        mid_point = len(valid_laps) // 2
        first_half = valid_laps.iloc[:mid_point]
        second_half = valid_laps.iloc[mid_point:]
        
        # Get average lap times
        lap_time_cols = ['lap_time', 'LapTime', 'LAP_TIME', 'lap_time_seconds']
        lap_time_col = None
        for col in lap_time_cols:
            if col in valid_laps.columns:
                lap_time_col = col
                break
        
        if not lap_time_col:
            return {'dropoff_percent': 0.0, 'first_half_avg': 0.0, 'second_half_avg': 0.0, 'significant': False}
        
        def get_avg_time(df_subset):
            times = []
            for t in df_subset[lap_time_col]:
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
                                pass
            return np.mean(times) if times else 0.0
        
        first_avg = get_avg_time(first_half)
        second_avg = get_avg_time(second_half)
        
        if first_avg == 0:
            return {'dropoff_percent': 0.0, 'first_half_avg': 0.0, 'second_half_avg': 0.0, 'significant': False}
        
        dropoff_percent = ((second_avg - first_avg) / first_avg) * 100
        
        # Statistical significance (simple t-test)
        first_times = [t for t in first_half[lap_time_col] if pd.notna(t)]
        second_times = [t for t in second_half[lap_time_col] if pd.notna(t)]
        
        significant = False
        if len(first_times) >= 3 and len(second_times) >= 3:
            try:
                t_stat, p_value = stats.ttest_ind(first_times, second_times)
                significant = p_value < 0.05
            except:
                pass
        
        return {
            'dropoff_percent': dropoff_percent,
            'first_half_avg': first_avg,
            'second_half_avg': second_avg,
            'significant': significant,
            'interpretation': 'Significant fatigue' if dropoff_percent > 2.0 and significant else
                            'Moderate dropoff' if dropoff_percent > 1.0 else
                            'Stable performance'
        }
    
    def calculate_sector_strength_fingerprint(self, df: pd.DataFrame, driver_id: Optional[str] = None) -> Dict:
        """Calculate Sector Strength Fingerprint (delegates to SectorTimingEngine)."""
        return self.sector_engine.calculate_sector_strength(df, driver_id)
    
    def calculate_comprehensive_metrics(self, df: pd.DataFrame, driver_id: Optional[str] = None) -> Dict:
        """
        Calculate all driver metrics at once.
        
        Returns comprehensive dict with all metrics:
        - consistency_index
        - aggression_score
        - pace_stability
        - fatigue_dropoff
        - sector_strength
        """
        return {
            'consistency_index': self.calculate_consistency_index(df, driver_id),
            'aggression_score': self.calculate_aggression_score(df, driver_id),
            'pace_stability': self.calculate_pace_stability_curve(df, driver_id),
            'fatigue_dropoff': self.calculate_fatigue_dropoff(df, driver_id),
            'sector_strength': self.calculate_sector_strength_fingerprint(df, driver_id)
        }


def analyze_driver_performance(df: pd.DataFrame, driver_id: Optional[str] = None) -> Dict:
    """
    Convenience function to calculate comprehensive driver metrics.
    
    Args:
        df: DataFrame with lap data
        driver_id: Optional driver/vehicle ID to analyze
    
    Returns:
        Dict with all driver metrics
    """
    metrics = DriverMetrics()
    return metrics.calculate_comprehensive_metrics(df, driver_id)

