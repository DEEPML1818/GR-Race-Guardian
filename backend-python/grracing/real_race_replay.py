"""
Real Race Replay Engine

Parses actual race data from CSV files and creates realistic race replay
with actual driver positions, lap times, and track positions.
"""

import csv
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None


class RealRaceReplay:
    """
    Creates realistic race replay from actual CSV data.
    """
    
    def __init__(self, tracks_base_path: Path):
        self.tracks_base_path = tracks_base_path
    
    def parse_real_lap_times(self, lap_time_file: Path) -> Dict:
        """
        Parse lap time CSV with actual timestamps and lap times.
        """
        if not PANDAS_AVAILABLE:
            # Fallback to CSV reader
            return self._parse_lap_times_csv(lap_time_file)
        
        lap_data = []
        
        try:
            df = pd.read_csv(lap_time_file, nrows=50000)  # Increased limit
            
            print(f"[RealRaceReplay] Loaded {len(df)} rows from {lap_time_file.name}")
            print(f"[RealRaceReplay] Columns: {list(df.columns)}")
            
            # Find relevant columns
            lap_col = None
            timestamp_col = None
            vehicle_id_col = None
            vehicle_number_col = None
            
            for col in df.columns:
                col_lower = col.lower()
                if 'lap' in col_lower and 'time' not in col_lower and 'start' not in col_lower and 'end' not in col_lower:
                    lap_col = col
                if 'timestamp' in col_lower:
                    timestamp_col = col
                if 'vehicle_id' in col_lower:
                    vehicle_id_col = col
                if 'vehicle_number' in col_lower:
                    vehicle_number_col = col
            
            print(f"[RealRaceReplay] Found columns - lap: {lap_col}, timestamp: {timestamp_col}, vehicle_id: {vehicle_id_col}, vehicle_number: {vehicle_number_col}")
            
            if not lap_col or not timestamp_col:
                return {"error": f"Required columns not found. Lap: {lap_col}, Timestamp: {timestamp_col}"}
            
            for idx, row in df.iterrows():
                try:
                    lap = row.get(lap_col)
                    timestamp = row.get(timestamp_col)
                    vehicle_id = row.get(vehicle_id_col) if vehicle_id_col else None
                    vehicle_number = row.get(vehicle_number_col) if vehicle_number_col else None
                    
                    if pd.notna(lap) and pd.notna(timestamp):
                        try:
                            lap_num = int(float(lap))
                            # Parse timestamp
                            if isinstance(timestamp, str):
                                try:
                                    ts = pd.to_datetime(timestamp)
                                except:
                                    ts = None
                            else:
                                ts = timestamp
                            
                            if ts and lap_num > 0:
                                lap_data.append({
                                    "lap": lap_num,
                                    "timestamp": ts.isoformat() if hasattr(ts, 'isoformat') else str(ts),
                                    "vehicle_id": str(vehicle_id) if vehicle_id else None,
                                    "vehicle_number": str(vehicle_number) if vehicle_number else None
                                })
                        except Exception as e:
                            continue
                except:
                    continue
            
            print(f"[RealRaceReplay] Parsed {len(lap_data)} lap records")
        
        except Exception as e:
            import traceback
            error_msg = f"Failed to parse lap times: {str(e)}\n{traceback.format_exc()}"
            print(f"[RealRaceReplay] Error: {error_msg}")
            return {"error": error_msg}
        
        # Group by vehicle
        by_vehicle = defaultdict(list)
        for lap in lap_data:
            key = lap.get("vehicle_id") or lap.get("vehicle_number") or "unknown"
            by_vehicle[key].append(lap)
        
        # Sort by lap for each vehicle
        for vehicle_id in by_vehicle:
            by_vehicle[vehicle_id].sort(key=lambda x: x["lap"])
        
        print(f"[RealRaceReplay] Found {len(by_vehicle)} vehicles")
        
        return {
            "lap_times": dict(by_vehicle),
            "total_vehicles": len(by_vehicle)
        }
    
    def _parse_lap_times_csv(self, lap_time_file: Path) -> Dict:
        """Fallback CSV parser without pandas."""
        lap_data = []
        
        try:
            with open(lap_time_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    lap = row.get('lap') or row.get('LAP')
                    timestamp = row.get('timestamp') or row.get('TIMESTAMP')
                    vehicle_id = row.get('vehicle_id') or row.get('VEHICLE_ID')
                    vehicle_number = row.get('vehicle_number') or row.get('VEHICLE_NUMBER') or row.get('NUMBER')
                    
                    if lap and timestamp:
                        try:
                            lap_num = int(float(lap))
                            if lap_num > 0:
                                lap_data.append({
                                    "lap": lap_num,
                                    "timestamp": timestamp,
                                    "vehicle_id": str(vehicle_id) if vehicle_id else None,
                                    "vehicle_number": str(vehicle_number) if vehicle_number else None
                                })
                        except:
                            continue
        except Exception as e:
            return {"error": f"Failed to parse CSV: {str(e)}"}
        
        # Group by vehicle
        by_vehicle = defaultdict(list)
        for lap in lap_data:
            key = lap.get("vehicle_id") or lap.get("vehicle_number") or "unknown"
            by_vehicle[key].append(lap)
        
        for vehicle_id in by_vehicle:
            by_vehicle[vehicle_id].sort(key=lambda x: x["lap"])
        
        return {
            "lap_times": dict(by_vehicle),
            "total_vehicles": len(by_vehicle)
        }
    
    def calculate_race_positions(self, lap_times_data: Dict, results_data: List[Dict]) -> List[Dict]:
        """
        Calculate actual race positions for each lap based on cumulative time.
        """
        if "error" in lap_times_data or not lap_times_data.get("lap_times"):
            print(f"[RealRaceReplay] No lap times data: {lap_times_data}")
            return []
        
        lap_times = lap_times_data["lap_times"]
        print(f"[RealRaceReplay] Calculating positions for {len(lap_times)} vehicles")
        
        # Get vehicle numbers from results and create mapping
        vehicle_map = {}  # {vehicle_id_from_lap_times: vehicle_number_from_results}
        results_map = {}  # {vehicle_number: result_data}
        
        for result in results_data:
            vehicle_number = str(result.get("vehicle_number", "")).strip()
            if vehicle_number:
                results_map[vehicle_number] = result
                # Try to match with lap time data
                for vid in lap_times.keys():
                    vid_str = str(vid).strip()
                    vehicle_num_str = str(vehicle_number).strip()
                    # Match if vehicle number appears in vehicle_id or vice versa
                    if vehicle_num_str in vid_str or vid_str in vehicle_num_str:
                        vehicle_map[vid] = vehicle_number
                        break
                    # Also try matching last digits
                    if vehicle_num_str.isdigit() and vid_str.endswith(vehicle_num_str):
                        vehicle_map[vid] = vehicle_number
                        break
        
        print(f"[RealRaceReplay] Mapped {len(vehicle_map)} vehicles")
        
        # Calculate cumulative times per lap
        max_lap = 0
        cumulative_times = defaultdict(dict)  # {vehicle_id: {lap: cumulative_time}}
        lap_times_dict = {}  # {vehicle_id: {lap: lap_time_seconds}}
        
        for vehicle_id, laps in lap_times.items():
            cumulative = 0.0
            prev_timestamp = None
            
            for lap_info in sorted(laps, key=lambda x: x["lap"]):
                lap_num = lap_info["lap"]
                max_lap = max(max_lap, lap_num)
                
                # Calculate lap time from timestamps
                try:
                    if PANDAS_AVAILABLE:
                        curr_ts = pd.to_datetime(lap_info["timestamp"])
                    else:
                        # Parse ISO format manually
                        from datetime import datetime
                        curr_ts = datetime.fromisoformat(lap_info["timestamp"].replace('Z', '+00:00'))
                    
                    if prev_timestamp:
                        if PANDAS_AVAILABLE:
                            lap_time_seconds = (curr_ts - prev_timestamp).total_seconds()
                        else:
                            lap_time_seconds = (curr_ts - prev_timestamp).total_seconds()
                        
                        # Reasonable lap time range (60-300 seconds)
                        if 60 < lap_time_seconds < 300:
                            cumulative += lap_time_seconds
                            if vehicle_id not in lap_times_dict:
                                lap_times_dict[vehicle_id] = {}
                            lap_times_dict[vehicle_id][lap_num] = lap_time_seconds
                    else:
                        # First lap - estimate from average
                        cumulative += 100.0  # Default 100 seconds
                        if vehicle_id not in lap_times_dict:
                            lap_times_dict[vehicle_id] = {}
                        lap_times_dict[vehicle_id][lap_num] = 100.0
                    
                    prev_timestamp = curr_ts
                    cumulative_times[vehicle_id][lap_num] = cumulative
                except Exception as e:
                    # If timestamp parsing fails, use estimated time
                    cumulative += 100.0
                    cumulative_times[vehicle_id][lap_num] = cumulative
                    if vehicle_id not in lap_times_dict:
                        lap_times_dict[vehicle_id] = {}
                    lap_times_dict[vehicle_id][lap_num] = 100.0
        
        print(f"[RealRaceReplay] Max lap: {max_lap}, Calculated times for {len(cumulative_times)} vehicles")
        
        # Calculate positions per lap
        lap_positions = []
        
        for lap_num in range(1, max_lap + 1):
            # Get cumulative times for this lap
            lap_cumulative = []
            for vehicle_id, lap_times_dict_laps in cumulative_times.items():
                if lap_num in lap_times_dict_laps:
                    # Get vehicle number from map or use vehicle_id
                    vehicle_number = vehicle_map.get(vehicle_id, vehicle_id)
                    
                    lap_cumulative.append({
                        "vehicle_id": vehicle_id,
                        "vehicle_number": vehicle_number,
                        "cumulative_time": lap_times_dict_laps[lap_num],
                        "lap": lap_num
                    })
            
            # Sort by cumulative time (lower = ahead)
            lap_cumulative.sort(key=lambda x: x["cumulative_time"])
            
            # Assign positions
            positions = []
            for idx, driver in enumerate(lap_cumulative):
                positions.append({
                    "vehicle_id": driver["vehicle_id"],
                    "vehicle_number": driver["vehicle_number"],
                    "lap": lap_num,
                    "position": idx + 1,
                    "cumulative_time": driver["cumulative_time"]
                })
            
            if positions:
                lap_positions.append({
                    "lap": lap_num,
                    "positions": positions
                })
        
        print(f"[RealRaceReplay] Calculated positions for {len(lap_positions)} laps")
        return lap_positions
    
    def get_real_race_replay(self, track_id: str, race_id: str, track_info: Dict) -> Dict:
        """
        Get complete real race replay data.
        """
        from .track_data_parser import TrackDataParser
        
        parser = TrackDataParser()
        parser.tracks_base_path = self.tracks_base_path
        
        # Get results first
        print(f"[RealRaceReplay] Getting results for {track_id}, {race_id}")
        results = parser.parse_race_results(track_id, race_id)
        if "error" in results:
            print(f"[RealRaceReplay] Error getting results: {results['error']}")
            return {"error": results["error"]}
        
        print(f"[RealRaceReplay] Got {len(results.get('results', []))} results")
        
        # Get lap time file
        track_path = self.tracks_base_path / track_info["path"]
        lap_time_files = []
        
        # Find lap time file
        for race_dir in ["Race 1", "Race 2", "race-1", "race-2"]:
            race_path = track_path / race_dir
            if race_path.exists():
                files = list(race_path.glob("*lap_time*.csv"))
                if files:
                    lap_time_files.extend(files)
                    break
        
        if not lap_time_files:
            lap_time_files = list(track_path.glob("*lap_time*.csv"))
        
        # Filter by race
        if lap_time_files and race_id:
            if "race-1" in race_id.lower() or "1" in race_id:
                lap_time_files = [f for f in lap_time_files if 'R1' in f.name.upper()]
            elif "race-2" in race_id.lower() or "2" in race_id:
                lap_time_files = [f for f in lap_time_files if 'R2' in f.name.upper()]
        
        if not lap_time_files:
            print(f"[RealRaceReplay] No lap time files found in {track_path}")
            # Return results only if no lap times
            return {
                "track_id": track_id,
                "race_id": race_id,
                "results": results["results"],
                "lap_progression": [],
                "total_laps": 0,
                "total_drivers": len(results["results"]),
                "warning": "No lap time data available"
            }
        
        print(f"[RealRaceReplay] Using lap time file: {lap_time_files[0].name}")
        
        # Parse real lap times
        lap_times_data = self.parse_real_lap_times(lap_time_files[0])
        if "error" in lap_times_data:
            print(f"[RealRaceReplay] Error parsing lap times: {lap_times_data['error']}")
            # Return results only if lap times fail
            return {
                "track_id": track_id,
                "race_id": race_id,
                "results": results["results"],
                "lap_progression": [],
                "total_laps": 0,
                "total_drivers": len(results["results"]),
                "warning": f"Lap time parsing failed: {lap_times_data['error']}"
            }
        
        print(f"[RealRaceReplay] Parsed lap times for {lap_times_data.get('total_vehicles', 0)} vehicles")
        
        # Calculate positions
        lap_positions = self.calculate_race_positions(lap_times_data, results["results"])
        
        return {
            "track_id": track_id,
            "race_id": race_id,
            "results": results["results"],
            "lap_progression": lap_positions,
            "total_laps": len(lap_positions),
            "total_drivers": len(results["results"])
        }
        """
        Get complete real race replay data.
        """
        from .track_data_parser import TrackDataParser
        
        parser = TrackDataParser()
        parser.tracks_base_path = self.tracks_base_path
        
        # Get results
        results = parser.parse_race_results(track_id, race_id)
        if "error" in results:
            return {"error": results["error"]}
        
        # Get lap time file
        track_path = self.tracks_base_path / track_info["path"]
        lap_time_files = []
        
        # Find lap time file
        for race_dir in ["Race 1", "Race 2", "race-1", "race-2"]:
            race_path = track_path / race_dir
            if race_path.exists():
                files = list(race_path.glob("*lap_time*.csv"))
                if files:
                    lap_time_files.extend(files)
                    break
        
        if not lap_time_files:
            lap_time_files = list(track_path.glob("*lap_time*.csv"))
        
        # Filter by race
        if lap_time_files and race_id:
            if "race-1" in race_id.lower() or "1" in race_id:
                lap_time_files = [f for f in lap_time_files if 'R1' in f.name.upper()]
            elif "race-2" in race_id.lower() or "2" in race_id:
                lap_time_files = [f for f in lap_time_files if 'R2' in f.name.upper()]
        
        if not lap_time_files:
            return {"error": "Lap time file not found"}
        
        # Parse real lap times
        lap_times_data = self.parse_real_lap_times(lap_time_files[0])
        if "error" in lap_times_data:
            return {"error": lap_times_data["error"]}
        
        # Calculate positions
        lap_positions = self.calculate_race_positions(lap_times_data, results["results"])
        
        return {
            "track_id": track_id,
            "race_id": race_id,
            "results": results["results"],
            "lap_progression": lap_positions,
            "total_laps": len(lap_positions),
            "total_drivers": len(results["results"])
        }
    
    def get_driver_track_positions(self, lap_num: int, lap_positions: List[Dict], 
                                   track_coordinates: List[Dict]) -> List[Dict]:
        """
        Calculate actual positions on track for a given lap.
        Uses cumulative time to determine position around track.
        """
        if not lap_positions or lap_num < 1:
            return []
        
        # Find lap data
        lap_data = next((l for l in lap_positions if l["lap"] == lap_num), None)
        if not lap_data:
            return []
        
        positions = lap_data["positions"]
        if not positions:
            return []
        
        # Calculate track positions based on cumulative time
        # Leader is at start/finish, others are behind based on time gap
        leader_time = positions[0]["cumulative_time"] if positions else 0
        track_length = len(track_coordinates) if track_coordinates else 100
        
        driver_positions = []
        for driver in positions:
            time_gap = driver["cumulative_time"] - leader_time
            
            # Estimate position on track (0-1, where 0 is start/finish)
            # Assume average lap time of 100 seconds, track has ~100 points
            avg_lap_time = 100.0
            position_on_track = (time_gap / avg_lap_time) % 1.0
            
            # Convert to track coordinate index
            track_index = int(position_on_track * track_length) % track_length
            
            if track_index < len(track_coordinates):
                coord = track_coordinates[track_index]
                driver_positions.append({
                    "vehicle_number": driver["vehicle_number"],
                    "position": driver["position"],
                    "x": coord.get("x", 0.5),
                    "y": coord.get("y", 0.5),
                    "lap": lap_num,
                    "time_gap": time_gap
                })
        
        return driver_positions

