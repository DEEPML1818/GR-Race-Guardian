"""
Sector Timing Engine - FIA-style sector analysis for racing telemetry.

This module provides professional-grade sector timing analysis used in
Formula 1, WEC, IndyCar, and IMSA race engineering systems.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from enum import Enum


class SectorType(Enum):
    """Sector classifications for timing analysis."""
    SECTOR_1 = "S1"
    SECTOR_2 = "S2"
    SECTOR_3 = "S3"
    COMBINED = "FULL_LAP"


class SectorTimingEngine:
    """
    Professional sector timing engine for race analysis.
    
    Handles:
    - Sector time extraction from telemetry
    - Delta-to-best calculations
    - Sector strength analysis
    - Sector time improvements/degradation
    """
    
    def __init__(self, sector_count: int = 3):
        """
        Initialize sector timing engine.
        
        Args:
            sector_count: Number of sectors (typically 3 for most circuits)
        """
        self.sector_count = sector_count
        self.sector_columns = [f"S{i}" for i in range(1, sector_count + 1)]
        self.best_sectors = {}
        self.best_lap_time = None
    
    def extract_sectors_from_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract sector times from dataframe.
        
        Looks for columns: S1, S2, S3 or S1_SECONDS, S2_SECONDS, S3_SECONDS
        """
        result_df = df.copy()
        
        # Try different column naming conventions
        sector_cols = []
        for i in range(1, self.sector_count + 1):
            for pattern in [f"S{i}", f"S{i}_SECONDS", f"SECTOR_{i}"]:
                if pattern in df.columns:
                    sector_cols.append(pattern)
                    result_df[f"sector_{i}_seconds"] = self._parse_time_to_seconds(
                        df[pattern]
                    )
                    break
        
        return result_df
    
    def _parse_time_to_seconds(self, time_series: pd.Series) -> pd.Series:
        """Convert time strings (MM:SS.mmm or HH:MM:SS.mmm) to seconds."""
        if time_series.dtype == 'float64' or time_series.dtype == 'int64':
            return time_series
        
        def parse_time(t):
            if pd.isna(t):
                return np.nan
            if isinstance(t, (int, float)):
                return float(t)
            
            parts = str(t).split(':')
            if len(parts) == 3:  # HH:MM:SS.mmm
                hours, minutes, seconds = map(float, parts)
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:  # MM:SS.mmm
                minutes, seconds = map(float, parts)
                return minutes * 60 + seconds
            else:
                return float(t) if t else np.nan
        
        return time_series.apply(parse_time)
    
    def calculate_delta_to_best(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate delta-to-best for each sector and full lap.
        
        Returns dataframe with delta columns: delta_s1, delta_s2, delta_s3, delta_lap
        """
        result_df = df.copy()
        
        # Calculate best times
        for i in range(1, self.sector_count + 1):
            col = f"sector_{i}_seconds"
            if col in result_df.columns:
                best = result_df[col].min()
                self.best_sectors[f"S{i}"] = best
                result_df[f"delta_s{i}"] = result_df[col] - best
        
        # Calculate best lap time
        lap_time_cols = ['lap_time', 'LapTime', 'LAP_TIME', 'lap_time_seconds']
        lap_time_col = None
        for col in lap_time_cols:
            if col in result_df.columns:
                lap_time_col = col
                break
        
        if lap_time_col:
            lap_times = self._parse_time_to_seconds(result_df[lap_time_col])
            self.best_lap_time = lap_times.min()
            result_df['delta_lap'] = lap_times - self.best_lap_time
        
        return result_df
    
    def calculate_sector_strength(self, df: pd.DataFrame, driver_id: Optional[str] = None) -> Dict:
        """
        Calculate sector strength fingerprint for a driver.
        
        Returns dict with:
        - sector_strengths: relative performance in each sector
        - best_sector: which sector driver is strongest
        - worst_sector: which sector driver is weakest
        """
        if driver_id:
            driver_df = df[df.get('vehicle_id', '') == driver_id] if 'vehicle_id' in df.columns else df
        else:
            driver_df = df
        
        sector_strengths = {}
        sector_means = {}
        
        for i in range(1, self.sector_count + 1):
            col = f"sector_{i}_seconds"
            if col in driver_df.columns:
                mean_time = driver_df[col].mean()
                best_time = driver_df[col].min()
                sector_strengths[f"S{i}"] = (best_time / mean_time) * 100
                sector_means[f"S{i}"] = mean_time
        
        # Find best and worst sectors
        if sector_strengths:
            best_sector = max(sector_strengths.items(), key=lambda x: x[1])
            worst_sector = min(sector_strengths.items(), key=lambda x: x[1])
            
            return {
                'sector_strengths': sector_strengths,
                'sector_means': sector_means,
                'best_sector': best_sector[0],
                'worst_sector': worst_sector[0],
                'strength_index': best_sector[1] / worst_sector[1] if worst_sector[1] > 0 else 1.0
            }
        
        return {}
    
    def analyze_sector_improvements(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze sector-by-sector improvements across laps.
        
        Adds columns: s1_improvement, s2_improvement, s3_improvement
        """
        result_df = df.copy().sort_values(by=['lap', 'vehicle_id'] if 'lap' in df.columns and 'vehicle_id' in df.columns else 'index')
        
        for i in range(1, self.sector_count + 1):
            col = f"sector_{i}_seconds"
            if col in result_df.columns:
                result_df[f"s{i}_improvement"] = result_df.groupby('vehicle_id')[col].diff() * -1  # Negative = improvement
        
        return result_df
    
    def get_delta_to_leader(self, df: pd.DataFrame, reference_driver: Optional[str] = None) -> pd.DataFrame:
        """
        Calculate delta-to-leader for all drivers.
        
        Args:
            df: DataFrame with lap times
            reference_driver: Optional driver ID to use as reference (otherwise uses fastest)
        """
        result_df = df.copy()
        
        lap_time_cols = ['lap_time', 'LapTime', 'LAP_TIME', 'lap_time_seconds']
        lap_time_col = None
        for col in lap_time_cols:
            if col in result_df.columns:
                lap_time_col = col
                break
        
        if not lap_time_col:
            return result_df
        
        lap_times = self._parse_time_to_seconds(result_df[lap_time_col])
        
        if reference_driver and 'vehicle_id' in result_df.columns:
            ref_times = result_df[result_df['vehicle_id'] == reference_driver][lap_time_col]
            if len(ref_times) > 0:
                reference_time = self._parse_time_to_seconds(ref_times).iloc[0]
            else:
                reference_time = lap_times.min()
        else:
            reference_time = lap_times.min()
        
        result_df['delta_to_leader'] = lap_times - reference_time
        
        return result_df


def analyze_sector_performance(df: pd.DataFrame, driver_id: Optional[str] = None) -> Dict:
    """
    Convenience function to analyze sector performance for a driver.
    
    Returns comprehensive sector analysis including:
    - Sector strengths
    - Best/worst sectors
    - Consistency metrics
    """
    engine = SectorTimingEngine()
    df_with_sectors = engine.extract_sectors_from_df(df)
    df_with_delta = engine.calculate_delta_to_best(df_with_sectors)
    sector_strength = engine.calculate_sector_strength(df_with_delta, driver_id)
    
    # Calculate consistency
    consistency = {}
    for i in range(1, 4):
        col = f"sector_{i}_seconds"
        if col in df_with_delta.columns:
            std_dev = df_with_delta[col].std()
            mean_time = df_with_delta[col].mean()
            consistency[f"S{i}"] = 1.0 - (std_dev / mean_time) if mean_time > 0 else 0.0
    
    return {
        **sector_strength,
        'consistency': consistency,
        'overall_consistency': np.mean(list(consistency.values())) if consistency else 0.0
    }

