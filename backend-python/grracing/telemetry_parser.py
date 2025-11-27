"""
Telemetry Parser

Parses telemetry CSV data and generates GPS-based replay data.
Handles wide-format telemetry with telemetry_name/telemetry_value columns.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from .track_coordinates import TrackCoordinates
from .gps_coordinates import GPSTrackCoordinates


class TelemetryParser:
    """
    Parse telemetry CSV and generate position data for race replay.
    """
    
    def __init__(self, track_id: str):
        self.track_id = track_id
        self.track_coords = TrackCoordinates()
        self.gps_coords = GPSTrackCoordinates()
        
    def parse_telemetry_csv(self, csv_path: str) -> pd.DataFrame:
        """
        Parse telemetry CSV in wide format.
        
        Expected columns:
        - telemetry_name: Name of the telemetry channel
        - telemetry_value: Value of the telemetry
        - timestamp: Timestamp of the reading
        - vehicle_number: Car number
        - lap: Lap number
        """
        df = pd.read_csv(csv_path)
        
        # Pivot to get one row per timestamp/vehicle with columns for each telemetry type
        df_pivot = df.pivot_table(
            index=['timestamp', 'vehicle_number', 'lap'],
            columns='telemetry_name',
            values='telemetry_value',
            aggfunc='first'
        ).reset_index()
        
        return df_pivot
    
    def build_track_path_gps(self) -> List[Tuple[float, float]]:
        """
        Build GPS track path from normalized coordinates.
        
        Returns:
            List of (lat, lon) tuples forming the track outline
        """
        track_data = self.track_coords.get_track_coordinates(self.track_id)
        if not track_data or "coordinates" not in track_data:
            return []
        
        normalized_coords = track_data["coordinates"]
        gps_path = self.gps_coords.normalize_to_gps(self.track_id, normalized_coords)
        
        return gps_path
    
    def interpolate_position(
        self,
        vehicle_df: pd.DataFrame,  # Changed from lap_times_df to pre-filtered vehicle_df
        timestamp: datetime
    ) -> Optional[Dict]:
        """
        Interpolate car position at a specific timestamp.
        
        Args:
            vehicle_df: DataFrame with lap timing data for a specific vehicle
            timestamp: Target timestamp
            
        Returns:
            Dict with position info or None
        """
        if vehicle_df.empty:
            return None
        
        # Find surrounding data points
        # Optimization: Use searchsorted if timestamps are sorted (they should be)
        # But for now, simple filtering is okay if df is small (per vehicle)
        
        # Ensure timestamp is datetime
        if not isinstance(timestamp, pd.Timestamp):
            timestamp = pd.to_datetime(timestamp)
            
        # We assume vehicle_df is already sorted by timestamp
        
        # Use searchsorted for O(log n) lookup instead of O(n) filtering
        # timestamps = vehicle_df['timestamp'].values
        # idx = np.searchsorted(timestamps, timestamp)
        
        # Keeping it simple but robust for now:
        before = vehicle_df[vehicle_df['timestamp'] <= timestamp]
        after = vehicle_df[vehicle_df['timestamp'] > timestamp]
        
        if before.empty:
            # Before race start
            row = vehicle_df.iloc[0]
            lap_progress = 0.0
        elif after.empty:
            # After race end
            row = vehicle_df.iloc[-1]
            lap_progress = 1.0
        else:
            # Interpolate
            row_before = before.iloc[-1]
            row_after = after.iloc[0]
            
            # Calculate progress between these two points
            time_diff = (row_after['timestamp'] - row_before['timestamp']).total_seconds()
            time_since = (timestamp - row_before['timestamp']).total_seconds()
            
            if time_diff > 0:
                ratio = time_since / time_diff
            else:
                ratio = 0
            
            # Use lap number to determine overall progress
            # lap = row_before['lap']
            lap_progress = ratio  # Progress within current lap
            row = row_before
        
        return {
            'vehicle_number': int(row['vehicle_number']),
            'lap': int(row['lap']),
            'lap_progress': lap_progress,
            'timestamp': timestamp
        }
    
    def calculate_track_position(self, lap_progress: float) -> Tuple[float, float]:
        """
        Calculate GPS position on track given lap progress (0-1).
        
        Args:
            lap_progress: Progress through lap (0.0 to 1.0)
            
        Returns:
            (lat, lon) tuple
        """
        track_path = self.build_track_path_gps()
        if not track_path:
            # Fallback to track center
            track_gps = self.gps_coords.get_track_gps(self.track_id)
            if track_gps and "center" in track_gps:
                return tuple(track_gps["center"])
            return (0.0, 0.0)
        
        # Find position along path
        progress_clamped = max(0.0, min(1.0, lap_progress))
        index = int(progress_clamped * (len(track_path) - 1))
        index = min(index, len(track_path) - 1)
        
        # Interpolate between points for smoother movement
        if index < len(track_path) - 1:
            next_index = index + 1
            local_progress = (progress_clamped * (len(track_path) - 1)) - index
            
            lat1, lon1 = track_path[index]
            lat2, lon2 = track_path[next_index]
            
            lat = lat1 + (lat2 - lat1) * local_progress
            lon = lon1 + (lon2 - lon1) * local_progress
            
            return (lat, lon)
        
        return track_path[index]
    
    def build_telemetry_replay(
        self,
        lap_times_csv: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        time_step: float = 1.0  # Changed default to 1.0s for performance
    ) -> Dict:
        """
        Build complete telemetry-based replay data.
        
        Args:
            lap_times_csv: Path to lap times CSV
            start_time: Optional start time (uses first timestamp if None)
            end_time: Optional end time (uses last timestamp if None)
            time_step: Time interval between position updates (seconds)
            
        Returns:
            Dict with replay data including GPS positions over time
        """
        # Parse lap times
        lap_times_df = pd.read_csv(lap_times_csv)
        lap_times_df['timestamp'] = pd.to_datetime(lap_times_df['timestamp'])
        
        # Determine time range
        if start_time is None:
            start_time = lap_times_df['timestamp'].min()
        if end_time is None:
            end_time = lap_times_df['timestamp'].max()
        
        # Get unique vehicles
        vehicles = sorted(lap_times_df['vehicle_number'].unique())
        
        # Pre-filter dataframes for each vehicle to avoid repeated filtering in loop
        vehicle_dfs = {}
        for vehicle in vehicles:
            v_df = lap_times_df[lap_times_df['vehicle_number'] == vehicle].sort_values('timestamp')
            vehicle_dfs[vehicle] = v_df
        
        # Build track path
        track_path_gps = self.build_track_path_gps()
        
        # Generate time series
        current_time = start_time
        replay_frames = []
        
        # Limit total frames to avoid timeout (e.g. max 3600 frames = 1 hour at 1fps)
        # If race is longer, increase time_step automatically?
        duration = (end_time - start_time).total_seconds()
        if duration > 3600 and time_step < 1.0:
            time_step = 1.0
        
        while current_time <= end_time:
            frame = {
                'timestamp': current_time.isoformat(),
                'time_seconds': (current_time - start_time).total_seconds(),
                'cars': []
            }
            
            for vehicle in vehicles:
                # Pass pre-filtered dataframe
                pos_info = self.interpolate_position(vehicle_dfs[vehicle], current_time)
                
                if pos_info:
                    # Calculate GPS position
                    lat, lon = self.calculate_track_position(pos_info['lap_progress'])
                    
                    frame['cars'].append({
                        'vehicle_number': int(vehicle),
                        'lap': pos_info['lap'],
                        'lap_progress': pos_info['lap_progress'],
                        'position': {
                            'lat': lat,
                            'lon': lon
                        }
                    })
            
            replay_frames.append(frame)
            current_time += pd.Timedelta(seconds=time_step)
        
        # Build complete replay structure
        track_gps = self.gps_coords.get_track_gps(self.track_id)
        track_info = self.track_coords.get_track_coordinates(self.track_id)
        
        replay_data = {
            'track_id': self.track_id,
            'track_name': track_info.get('name', 'Unknown'),
            'track_gps': track_gps,
            'track_path': [{'lat': lat, 'lon': lon} for lat, lon in track_path_gps],
            'duration_seconds': duration,
            'frames': replay_frames,
            'vehicles': [int(v) for v in vehicles]
        }
        
        return replay_data


def parse_telemetry(track_id: str, lap_times_csv: str) -> Dict:
    """
    Convenience function to parse telemetry and build replay.
    
    Args:
        track_id: Track identifier
        lap_times_csv: Path to lap times CSV
        
    Returns:
        Complete replay data structure
    """
    parser = TelemetryParser(track_id)
    return parser.build_telemetry_replay(lap_times_csv)
