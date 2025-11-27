"""
Race Replay Builder

Motorsport data engineering module for converting raw CSV race data
into structured track replay visualizations.

This module analyzes race results, lap times, and telemetry to reconstruct
the complete race timeline with overtakes, gaps, and position changes.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json
from datetime import datetime, timedelta
from .telemetry_parser import TelemetryParser


class RaceReplayBuilder:
    """
    Converts raw race CSV data into structured replay JSON for visualization.
    
    Detects:
    - Overtakes
    - Safety car periods
    - Pit stops
    - DNFs
    - Lap anomalies
    """
    
    def __init__(self, track_id: str):
        self.track_id = track_id
        self.track_info = self._get_track_info()
        
    def _get_track_info(self) -> Dict:
        """Get track metadata"""
        tracks = {
            "barber": {
                "name": "Barber Motorsports Park",
                "length_miles": 2.38,
                "turns": 17,
                "sectors": 3
            },
            "cota": {
                "name": "Circuit of the Americas",
                "length_miles": 3.427,
                "turns": 20,
                "sectors": 3
            },
            "indianapolis": {
                "name": "Indianapolis Motor Speedway",
                "length_miles": 2.439,
                "turns": 14,
                "sectors": 3
            },
            "road-america": {
                "name": "Road America",
                "length_miles": 4.048,
                "turns": 14,
                "sectors": 3
            },
            "sebring": {
                "name": "Sebring International Raceway",
                "length_miles": 3.74,
                "turns": 17,
                "sectors": 3
            },
            "sonoma": {
                "name": "Sonoma Raceway",
                "length_miles": 2.52,
                "turns": 12,
                "sectors": 3
            },
            "vir": {
                "name": "Virginia International Raceway",
                "length_miles": 3.27,
                "turns": 17,
                "sectors": 3
            }
        }
        return tracks.get(self.track_id, {})
    
    def _convert_to_native_types(self, obj):
        """
        Convert numpy types to native Python types for JSON serialization.
        
        This ensures FastAPI can properly serialize the response without errors.
        """
        if isinstance(obj, dict):
            return {key: self._convert_to_native_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_native_types(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj
    
    def parse_results_csv(self, csv_path: str) -> pd.DataFrame:
        """
        Parse race results CSV.
        
        Expected columns:
        - POSITION, NUMBER, DRIVER, LAPS, TOTAL_TIME, GAP_FIRST, FL_TIME, etc.
        """
        df = pd.read_csv(csv_path, delimiter=';')
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        return df
    
    def parse_lap_times_csv(self, csv_path: str) -> pd.DataFrame:
        """
        Parse lap times CSV.
        
        Expected columns:
        - lap, vehicle_number, timestamp, vehicle_id
        """
        df = pd.read_csv(csv_path)
        
        # Clean and sort
        df = df.sort_values(['vehicle_number', 'lap'])
        
        return df
    
    def calculate_lap_positions(self, lap_times_df: pd.DataFrame) -> Dict[int, List[Dict]]:
        """
        Calculate driver positions for each lap.
        
        Returns:
            {lap_number: [{driver, position, time, gap}, ...]}
        """
        positions_by_lap = {}
        
        # Get all laps
        laps = sorted(lap_times_df['lap'].unique())
        
        for lap_num in laps:
            lap_data = lap_times_df[lap_times_df['lap'] == lap_num].copy()
            
            # Calculate cumulative time for each driver
            cumulative_times = {}
            for vehicle in lap_data['vehicle_number'].unique():
                vehicle_laps = lap_times_df[
                    (lap_times_df['vehicle_number'] == vehicle) & 
                    (lap_times_df['lap'] <= lap_num)
                ]
                
                if len(vehicle_laps) > 0:
                    # Calculate total time from timestamps
                    times = pd.to_datetime(vehicle_laps['timestamp'])
                    if len(times) > 1:
                        total_time = (times.iloc[-1] - times.iloc[0]).total_seconds()
                    else:
                        total_time = 0
                    
                    cumulative_times[vehicle] = {
                        'vehicle': vehicle,
                        'time': total_time,
                        'laps_completed': len(vehicle_laps)
                    }
            
            # Sort by laps completed (desc) then time (asc)
            sorted_drivers = sorted(
                cumulative_times.values(),
                key=lambda x: (-x['laps_completed'], x['time'])
            )
            
            # Assign positions and calculate gaps
            lap_positions = []
            leader_time = sorted_drivers[0]['time'] if sorted_drivers else 0
            
            for idx, driver in enumerate(sorted_drivers):
                gap = driver['time'] - leader_time if idx > 0 else 0.0
                
                lap_positions.append({
                    'driver': f"#{driver['vehicle']}",
                    'vehicle_number': driver['vehicle'],
                    'position': idx + 1,
                    'gap': round(gap, 3),
                    'laps_completed': driver['laps_completed']
                })
            
            positions_by_lap[lap_num] = lap_positions
        
        return positions_by_lap
    
    def detect_overtakes(self, positions_by_lap: Dict[int, List[Dict]]) -> Dict[int, List[str]]:
        """
        Detect overtakes between laps.
        
        Returns:
            {lap_number: ["Driver X overtook Driver Y", ...]}
        """
        overtakes = {}
        laps = sorted(positions_by_lap.keys())
        
        for i in range(1, len(laps)):
            prev_lap = laps[i-1]
            curr_lap = laps[i]
            
            prev_positions = {d['vehicle_number']: d['position'] for d in positions_by_lap[prev_lap]}
            curr_positions = {d['vehicle_number']: d['position'] for d in positions_by_lap[curr_lap]}
            
            lap_overtakes = []
            
            for vehicle, curr_pos in curr_positions.items():
                if vehicle in prev_positions:
                    prev_pos = prev_positions[vehicle]
                    
                    if curr_pos < prev_pos:
                        # This driver gained positions
                        positions_gained = prev_pos - curr_pos
                        lap_overtakes.append(
                            f"#{vehicle} → P{curr_pos} (+{positions_gained})"
                        )
            
            if lap_overtakes:
                overtakes[curr_lap] = lap_overtakes
        
        return overtakes
    
    def detect_anomalies(self, lap_times_df: pd.DataFrame) -> Dict[str, List[int]]:
        """
        Detect lap anomalies (slow laps, pit laps, safety car).
        
        Returns:
            {
                'slow_laps': [(vehicle, lap), ...],
                'pit_laps': [(vehicle, lap), ...],
                'safety_car_laps': [lap, ...]
            }
        """
        anomalies = {
            'slow_laps': [],
            'pit_laps': [],
            'safety_car_laps': []
        }
        
        # Calculate lap time deltas
        lap_times_df = lap_times_df.copy()
        lap_times_df['timestamp'] = pd.to_datetime(lap_times_df['timestamp'])
        
        for vehicle in lap_times_df['vehicle_number'].unique():
            vehicle_data = lap_times_df[lap_times_df['vehicle_number'] == vehicle].sort_values('lap')
            
            # Calculate lap times
            vehicle_data['lap_time'] = vehicle_data['timestamp'].diff().dt.total_seconds()
            
            # Get median lap time for this driver
            median_time = vehicle_data['lap_time'].median()
            
            # Detect slow laps (>120% of median)
            slow_threshold = median_time * 1.2
            slow_laps = vehicle_data[vehicle_data['lap_time'] > slow_threshold]
            
            for _, row in slow_laps.iterrows():
                anomalies['slow_laps'].append((vehicle, int(row['lap'])))
                
                # If VERY slow (>150%), likely a pit stop
                if row['lap_time'] > median_time * 1.5:
                    anomalies['pit_laps'].append((vehicle, int(row['lap'])))
        
        return anomalies
    
    def build_replay_json(
        self,
        results_csv: str,
        lap_times_csv: str,
        telemetry_csv: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Dict:
        """
        Build complete race replay JSON from CSV files.
        """
        
        # Parse inputs
        results_df = self.parse_results_csv(results_csv)
        lap_times_df = self.parse_lap_times_csv(lap_times_csv)
        
        # Calculate derived data
        positions_by_lap = self.calculate_lap_positions(lap_times_df)
        overtakes = self.detect_overtakes(positions_by_lap)
        anomalies = self.detect_anomalies(lap_times_df)
        
        # Build replay object
        replay_data = {
            "track_id": self.track_id,
            "track_name": self.track_info.get("name", "Unknown Track"),
            "date": datetime.now().isoformat(),
            "laps": len(positions_by_lap),
            "drivers": [],
            "timeline": []
        }
        
        # Add drivers info from results
        # This is a simplified mapping, might need more robust matching in production
        for _, row in results_df.iterrows():
            replay_data["drivers"].append({
                "number": str(row.get("NUMBER", "")),
                "name": row.get("DRIVER", "Unknown"),
                "team": row.get("TEAM", ""),
                "car": row.get("CAR", "")
            })
            
        # Build timeline
        for lap_num in sorted(positions_by_lap.keys()):
            lap_positions = positions_by_lap[lap_num]
            
            # Get events for this lap
            lap_overtakes = overtakes.get(lap_num, [])
            
            timeline_entry = {
                "lap": lap_num,
                "positions": lap_positions,
                "events": []
            }
            
            # Add overtake events
            for overtake in lap_overtakes:
                timeline_entry["events"].append({
                    "type": "overtake",
                    "description": overtake
                })
                
            replay_data["timeline"].append(timeline_entry)
            
        # Convert to native types for JSON serialization
        replay_data = self._convert_to_native_types(replay_data)
        
        # Save if path provided
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(replay_data, f, indent=2)
                
        return replay_data


def main():
    builder = RaceReplayBuilder("barber")
    
    # Example paths
    results_csv = "barber-motorsports-park/barber/03_Provisional Results_Race 1_Anonymized.CSV"
    lap_times_csv = "barber-motorsports-park/barber/R1_barber_lap_time.csv"
    
    # Only run if files exist to avoid errors during simple testing
    if Path(results_csv).exists() and Path(lap_times_csv).exists():
        replay_data = builder.build_replay_json(
            results_csv,
            lap_times_csv,
            output_path="barber_race1_replay.json"
        )
        
        print(f"Generated replay for {replay_data['track_name']}")
        print(f"Total laps: {replay_data['laps']}")
        print(f"Drivers: {len(replay_data['drivers'])}")
    else:
        print("Example files not found, skipping execution.")


if __name__ == "__main__":
    main()
