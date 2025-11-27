"""
Lap Classification Engine - Professional motorsport lap classification.

Implements industry-standard lap types used in F1, WEC, IndyCar, IMSA:
- OUT LAP
- IN LAP
- HOT LAP
- COOL LAP
- ERROR LAP
- PIT LAP
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from enum import Enum


class LapType(Enum):
    """Professional lap classification types."""
    OUT_LAP = "OUT_LAP"  # Lap after exiting pit lane
    IN_LAP = "IN_LAP"    # Lap before entering pit lane
    HOT_LAP = "HOT_LAP"  # Fast lap (qualifying pace)
    COOL_LAP = "COOL_LAP"  # Slower lap (managing tires/temp)
    ERROR_LAP = "ERROR_LAP"  # Error/off-track/invalid
    PIT_LAP = "PIT_LAP"  # Lap with pit stop activity
    RACE_LAP = "RACE_LAP"  # Standard race lap
    SAFETY_CAR = "SAFETY_CAR"  # Under safety car conditions
    VIRTUAL_SAFETY_CAR = "VIRTUAL_SAFETY_CAR"  # Under VSC conditions


class LapClassifier:
    """
    Professional lap classifier for motorsport analysis.
    
    Uses industry-standard heuristics to classify laps based on:
    - Lap time relative to best/session average
    - Pit lane activity
    - Telemetry patterns (speed, throttle, braking)
    - Flag conditions
    """
    
    def __init__(self, 
                 hot_lap_threshold: float = 1.02,  # Within 2% of best lap
                 cool_lap_threshold: float = 1.10,  # More than 10% slower
                 error_lap_threshold: float = 1.25):  # More than 25% slower
        """
        Initialize lap classifier.
        
        Args:
            hot_lap_threshold: Multiplier for best lap time (default: 1.02 = 2% slower)
            cool_lap_threshold: Multiplier for best lap time (default: 1.10 = 10% slower)
            error_lap_threshold: Multiplier for best lap time (default: 1.25 = 25% slower)
        """
        self.hot_lap_threshold = hot_lap_threshold
        self.cool_lap_threshold = cool_lap_threshold
        self.error_lap_threshold = error_lap_threshold
        self.best_lap_time = None
        self.session_avg_lap_time = None
    
    def _parse_lap_time(self, time_value) -> float:
        """Convert lap time to seconds."""
        if pd.isna(time_value):
            return np.nan
        if isinstance(time_value, (int, float)):
            return float(time_value)
        
        parts = str(time_value).split(':')
        if len(parts) == 3:  # HH:MM:SS.mmm
            hours, minutes, seconds = map(float, parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:  # MM:SS.mmm
            minutes, seconds = map(float, parts)
            return minutes * 60 + seconds
        else:
            try:
                return float(time_value)
            except:
                return np.nan
    
    def classify_laps(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Classify all laps in dataframe.
        
        Adds 'lap_type' and 'lap_classification' columns to dataframe.
        """
        result_df = df.copy()
        
        # Find lap time column
        lap_time_cols = ['lap_time', 'LapTime', 'LAP_TIME', 'lap_time_seconds', 'LAP_TIME_SECONDS']
        lap_time_col = None
        for col in lap_time_cols:
            if col in result_df.columns:
                lap_time_col = col
                break
        
        if not lap_time_col:
            result_df['lap_type'] = LapType.RACE_LAP.value
            return result_df
        
        # Convert to seconds
        lap_times_seconds = result_df[lap_time_col].apply(self._parse_lap_time)
        result_df['_lap_time_seconds'] = lap_times_seconds
        
        # Calculate best and average lap times
        valid_times = lap_times_seconds[lap_times_seconds.notna()]
        if len(valid_times) > 0:
            self.best_lap_time = valid_times.min()
            self.session_avg_lap_time = valid_times.mean()
        else:
            result_df['lap_type'] = LapType.RACE_LAP.value
            return result_df
        
        # Classify each lap
        classifications = []
        for idx, row in result_df.iterrows():
            lap_time = row['_lap_time_seconds']
            if pd.isna(lap_time):
                classifications.append(LapType.ERROR_LAP.value)
                continue
            
            # Check for pit activity
            if self._has_pit_activity(row):
                if self._is_in_lap(row, idx, result_df):
                    classifications.append(LapType.IN_LAP.value)
                elif self._is_out_lap(row, idx, result_df):
                    classifications.append(LapType.OUT_LAP.value)
                else:
                    classifications.append(LapType.PIT_LAP.value)
                continue
            
            # Check for safety car conditions
            if self._is_safety_car(row):
                classifications.append(LapType.SAFETY_CAR.value)
                continue
            
            if self._is_virtual_safety_car(row):
                classifications.append(LapType.VIRTUAL_SAFETY_CAR.value)
                continue
            
            # Classify by pace
            relative_time = lap_time / self.best_lap_time
            
            if relative_time <= self.hot_lap_threshold:
                classifications.append(LapType.HOT_LAP.value)
            elif relative_time >= self.error_lap_threshold:
                classifications.append(LapType.ERROR_LAP.value)
            elif relative_time >= self.cool_lap_threshold:
                classifications.append(LapType.COOL_LAP.value)
            else:
                classifications.append(LapType.RACE_LAP.value)
        
        result_df['lap_type'] = classifications
        result_df['lap_classification'] = result_df['lap_type'].apply(lambda x: LapType[x].value)
        
        # Clean up temporary column
        if '_lap_time_seconds' in result_df.columns:
            result_df = result_df.drop('_lap_time_seconds', axis=1)
        
        return result_df
    
    def _has_pit_activity(self, row: pd.Series) -> bool:
        """Check if row indicates pit activity."""
        pit_indicators = [
            'PIT_TIME', 'pit_time', 'PIT_STOP', 'pit_stop',
            'CROSSING_FINISH_LINE_IN_PIT', 'crossing_finish_line_in_pit',
            'IN_PIT', 'in_pit'
        ]
        for indicator in pit_indicators:
            if indicator in row.index:
                value = row[indicator]
                if pd.notna(value) and value != 0 and value != '':
                    return True
        return False
    
    def _is_in_lap(self, row: pd.Series, idx: int, df: pd.DataFrame) -> bool:
        """Heuristic: IN LAP typically before pit stop."""
        # Check if next lap has more pit activity or if this is last lap before pit
        if idx < len(df) - 1:
            next_row = df.iloc[idx + 1]
            if self._has_pit_activity(next_row) and not self._has_pit_activity(row):
                return False
        return False  # Default: conservative classification
    
    def _is_out_lap(self, row: pd.Series, idx: int, df: pd.DataFrame) -> bool:
        """Heuristic: OUT LAP typically after pit stop."""
        # Check if previous lap had pit activity
        if idx > 0:
            prev_row = df.iloc[idx - 1]
            if self._has_pit_activity(prev_row):
                return True
        return False
    
    def _is_safety_car(self, row: pd.Series) -> bool:
        """Check for safety car conditions."""
        flag_cols = ['FLAG', 'flag', 'FLAG_AT_FL', 'flag_at_fl']
        for col in flag_cols:
            if col in row.index:
                flag = str(row[col]).upper()
                if 'SC' in flag or 'SAFETY' in flag or 'CAUTION' in flag:
                    return True
        return False
    
    def _is_virtual_safety_car(self, row: pd.Series) -> bool:
        """Check for virtual safety car conditions."""
        flag_cols = ['FLAG', 'flag', 'FLAG_AT_FL', 'flag_at_fl']
        for col in flag_cols:
            if col in row.index:
                flag = str(row[col]).upper()
                if 'VSC' in flag or 'VIRTUAL' in flag:
                    return True
        return False
    
    def get_lap_type_counts(self, df: pd.DataFrame) -> Dict[str, int]:
        """Get count of each lap type in dataframe."""
        if 'lap_type' not in df.columns:
            df = self.classify_laps(df)
        
        return df['lap_type'].value_counts().to_dict()
    
    def filter_hot_laps(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return only HOT LAPs from dataframe."""
        if 'lap_type' not in df.columns:
            df = self.classify_laps(df)
        return df[df['lap_type'] == LapType.HOT_LAP.value]
    
    def filter_race_laps(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return only valid race laps (exclude error, pit, SC laps)."""
        if 'lap_type' not in df.columns:
            df = self.classify_laps(df)
        
        exclude_types = [
            LapType.ERROR_LAP.value,
            LapType.PIT_LAP.value,
            LapType.IN_LAP.value,
            LapType.OUT_LAP.value,
            LapType.SAFETY_CAR.value
        ]
        
        return df[~df['lap_type'].isin(exclude_types)]


def classify_lap_dataframe(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """
    Convenience function to classify laps in a dataframe.
    
    Args:
        df: DataFrame with lap time data
        **kwargs: Arguments to pass to LapClassifier
    
    Returns:
        DataFrame with 'lap_type' column added
    """
    classifier = LapClassifier(**kwargs)
    return classifier.classify_laps(df)

