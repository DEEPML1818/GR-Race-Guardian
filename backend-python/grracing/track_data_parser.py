"""
Track Data Parser

Parses CSV files from race tracks to extract race data for visualization and replay.
"""

import csv
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import json


class TrackDataParser:
    """
    Parser for track CSV data files.
    """
    
    def __init__(self):
        # Get the project root directory (3 levels up from this file)
        # backend-python/grracing/track_data_parser.py -> project root
        self.tracks_base_path = Path(__file__).parent.parent.parent
        # Debug: print the base path
        import os
        print(f"[TrackParser] Base path: {self.tracks_base_path}")
        print(f"[TrackParser] Base path exists: {self.tracks_base_path.exists()}")
        if self.tracks_base_path.exists():
            print(f"[TrackParser] Contents: {list(self.tracks_base_path.iterdir())[:10]}")
        
    def get_available_tracks(self) -> List[Dict]:
        """
        Get list of available tracks.
        """
        tracks = [
            {"id": "barber", "name": "Barber Motorsports Park", "path": "barber-motorsports-park/barber"},
            {"id": "cota", "name": "Circuit of the Americas", "path": "circuit-of-the-americas/COTA"},
            {"id": "indianapolis", "name": "Indianapolis Motor Speedway", "path": "indianapolis/indianapolis"},
            {"id": "road-america", "name": "Road America", "path": "road-america/road-america/Road America"},
            {"id": "sebring", "name": "Sebring International Raceway", "path": "sebring/sebring/Sebring"},
            {"id": "sonoma", "name": "Sonoma Raceway", "path": "sonoma/Sonoma"},
            {"id": "vir", "name": "Virginia International Raceway", "path": "virginia-international-raceway/virginia-international-raceway/VIR"}
        ]
        
        available = []
        for track in tracks:
            track_path = self.tracks_base_path / track["path"]
            print(f"[TrackParser] Checking track: {track['name']}")
            print(f"[TrackParser] Path: {track_path}")
            print(f"[TrackParser] Exists: {track_path.exists()}")
            
            if track_path.exists():
                # Check for race data
                races = self._find_races(track_path)
                print(f"[TrackParser] Found {len(races)} races for {track['name']}")
                
                # Always add track, even if no races found (user can still see track layout)
                track["races"] = races if races else [{"id": "race-1", "name": "Race 1", "path": str(track_path.relative_to(self.tracks_base_path))}]
                available.append(track)
            else:
                print(f"[TrackParser] Track path does not exist: {track_path}")
        
        print(f"[TrackParser] Returning {len(available)} available tracks")
        return available
    
    def _find_races(self, track_path: Path) -> List[Dict]:
        """Find available races for a track."""
        races = []
        
        print(f"[TrackParser] Finding races in: {track_path}")
        
        # Check for Race 1 and Race 2 directories
        for race_dir in ["Race 1", "Race 2"]:
            race_path = track_path / race_dir
            if race_path.exists():
                print(f"[TrackParser] Found race directory: {race_dir}")
                races.append({
                    "id": race_dir.lower().replace(" ", "-"),
                    "name": race_dir,
                    "path": str(race_path.relative_to(self.tracks_base_path))
                })
        
        # Check for direct race files (like barber)
        if not races:
            # Look for any CSV files
            lap_time_files = list(track_path.glob("*lap_time*.csv")) + list(track_path.glob("*lap_time*.CSV"))
            results_files = list(track_path.glob("*Results*.CSV")) + list(track_path.glob("*Results*.csv"))
            any_csv_files = list(track_path.glob("*.csv")) + list(track_path.glob("*.CSV"))
            
            print(f"[TrackParser] Found {len(lap_time_files)} lap time files")
            print(f"[TrackParser] Found {len(results_files)} results files")
            print(f"[TrackParser] Found {len(any_csv_files)} total CSV files")
            
            # Check for R1 and R2 files separately
            r1_files = [f for f in lap_time_files if 'R1' in f.name.upper() or 'race-1' in f.name.lower()]
            r2_files = [f for f in lap_time_files if 'R2' in f.name.upper() or 'race-2' in f.name.lower()]
            
            # If we have any CSV files, create at least one race
            if r1_files or results_files or (any_csv_files and not r2_files):
                races.append({
                    "id": "race-1",
                    "name": "Race 1",
                    "path": str(track_path.relative_to(self.tracks_base_path))
                })
            
            if r2_files:
                races.append({
                    "id": "race-2",
                    "name": "Race 2",
                    "path": str(track_path.relative_to(self.tracks_base_path))
                })
        
        print(f"[TrackParser] Returning {len(races)} races")
        return races
    
    def parse_race_results(self, track_id: str, race_id: str) -> Dict:
        """
        Parse race results CSV.
        
        Returns:
            Race results with positions, times, gaps
        """
        track_info = self._get_track_info(track_id)
        if not track_info:
            return {"error": "Track not found"}
        
        # Find results file
        track_path = self.tracks_base_path / track_info["path"]
        
        # Look for results file - check Race subdirectories first
        results_files = []
        for race_dir in ["Race 1", "Race 2", "race-1", "race-2"]:
            race_path = track_path / race_dir
            if race_path.exists():
                results_files = list(race_path.glob("*Results*.CSV")) + list(race_path.glob("*Results*.csv"))
                if results_files:
                    break
        
        # If not found in subdirectories, check directly in track path
        if not results_files:
            results_files = list(track_path.glob("*Results*.CSV")) + list(track_path.glob("*Results*.csv"))
        
        # Also check for race-specific files based on race_id
        if not results_files and race_id:
            # Try to match race_id to file patterns
            if "race-1" in race_id.lower() or "1" in race_id:
                results_files = list(track_path.glob("*Race*1*.CSV")) + list(track_path.glob("*Race*1*.csv"))
            elif "race-2" in race_id.lower() or "2" in race_id:
                results_files = list(track_path.glob("*Race*2*.CSV")) + list(track_path.glob("*Race*2*.csv"))
        
        if not results_files:
            return {"error": "Results file not found"}
        
        # Parse first results file
        results_file = results_files[0]
        results = []
        
        print(f"[TrackParser] Parsing results file: {results_file.name}")
        
        try:
            with open(results_file, 'r', encoding='utf-8-sig') as f:
                # Read first line to detect delimiter
                first_line = f.readline()
                f.seek(0)
                
                # Try semicolon delimiter first (common in racing CSVs)
                delimiter = ';' if ';' in first_line else ','
                reader = csv.DictReader(f, delimiter=delimiter)
                
                print(f"[TrackParser] Using delimiter: '{delimiter}', Columns: {reader.fieldnames}")
                
                row_count = 0
                for row in reader:
                    row_count += 1
                    # Try to get position - check multiple column names
                    position_val = row.get('POSITION') or row.get('position') or row.get('Position')
                    if position_val:
                        try:
                            position = int(float(str(position_val).strip()))
                            vehicle_number = str(row.get('NUMBER') or row.get('number') or row.get('VEHICLE_NUMBER') or row.get('VEHICLE') or '').strip()
                            total_time = str(row.get('TOTAL_TIME') or row.get('total_time') or row.get('TOTAL') or '').strip()
                            gap_first = str(row.get('GAP_FIRST') or row.get('gap_first') or row.get('GAP') or '').strip()
                            laps_val = row.get('LAPS') or row.get('laps') or row.get('Lap')
                            laps = int(float(str(laps_val).strip())) if laps_val else 0
                            
                            if vehicle_number and position > 0:
                                results.append({
                                    "position": position,
                                    "vehicle_number": vehicle_number,
                                    "total_time": total_time if total_time else 'N/A',
                                    "gap_first": gap_first if gap_first else 'N/A',
                                    "laps": laps,
                                    "status": str(row.get('STATUS') or row.get('status') or 'Classified').strip()
                                })
                        except Exception as e:
                            print(f"[TrackParser] Error parsing row {row_count}: {e}")
                            continue
                
                print(f"[TrackParser] Parsed {len(results)} results from {row_count} rows")
        except Exception as e:
            import traceback
            error_msg = f"Failed to parse results: {str(e)}\n{traceback.format_exc()}"
            print(f"[TrackParser] Error: {error_msg}")
            return {"error": error_msg}
        
        if not results:
            return {"error": "No results found in file"}
        
        return {
            "track_id": track_id,
            "race_id": race_id,
            "results": results,
            "total_drivers": len(results)
        }
    
    def parse_lap_times(self, track_id: str, race_id: str) -> Dict:
        """
        Parse lap time CSV files.
        
        Returns:
            Lap times organized by vehicle and lap
        """
        track_info = self._get_track_info(track_id)
        if not track_info:
            return {"error": "Track not found"}
        
        track_path = self.tracks_base_path / track_info["path"]
        
        # Find lap time file - check Race subdirectories first
        lap_time_files = []
        for race_dir in ["Race 1", "Race 2", "race-1", "race-2"]:
            race_path = track_path / race_dir
            if race_path.exists():
                files = list(race_path.glob("*lap_time*.csv"))
                if files:
                    lap_time_files.extend(files)
                    break  # Use first match
        
        # Check directly in track path
        if not lap_time_files:
            lap_time_files = list(track_path.glob("*lap_time*.csv"))
        
        # Filter by race_id if specified
        if lap_time_files and race_id:
            if "race-1" in race_id.lower() or "1" in race_id:
                lap_time_files = [f for f in lap_time_files if 'R1' in f.name.upper() or 'race-1' in f.name.lower()]
            elif "race-2" in race_id.lower() or "2" in race_id:
                lap_time_files = [f for f in lap_time_files if 'R2' in f.name.upper() or 'race-2' in f.name.lower()]
        
        if not lap_time_files:
            return {"error": "Lap time file not found"}
        
        # Parse lap times
        lap_times_by_vehicle = {}
        
        for lap_file in lap_time_files:
            try:
                with open(lap_file, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    
                    for row in reader:
                        vehicle_id = row.get('vehicle_id') or row.get('vehicle_number') or row.get('NUMBER')
                        lap = int(row.get('lap') or row.get('LAP') or 0)
                        timestamp = row.get('timestamp') or row.get('TIMESTAMP') or ''
                        
                        if vehicle_id and lap > 0:
                            if vehicle_id not in lap_times_by_vehicle:
                                lap_times_by_vehicle[vehicle_id] = []
                            
                            lap_times_by_vehicle[vehicle_id].append({
                                "lap": lap,
                                "timestamp": timestamp,
                                "vehicle_id": vehicle_id
                            })
            except Exception as e:
                continue
        
        # Sort by lap for each vehicle
        for vehicle_id in lap_times_by_vehicle:
            lap_times_by_vehicle[vehicle_id].sort(key=lambda x: x["lap"])
        
        return {
            "track_id": track_id,
            "race_id": race_id,
            "lap_times": lap_times_by_vehicle,
            "total_vehicles": len(lap_times_by_vehicle)
        }
    
    def get_race_replay_data(self, track_id: str, race_id: str) -> Dict:
        """
        Get complete race replay data using REAL race data.
        
        Returns:
            Race progression data for replay visualization
        """
        from .real_race_replay import RealRaceReplay
        
        print(f"[TrackParser] Getting race replay for {track_id}, {race_id}")
        
        # Use real race replay engine
        replay_engine = RealRaceReplay(self.tracks_base_path)
        track_info = self._get_track_info(track_id)
        
        if not track_info:
            print(f"[TrackParser] Track info not found for {track_id}")
            return {"error": "Track not found"}
        
        print(f"[TrackParser] Track info: {track_info}")
        
        # Get real race replay
        replay_data = replay_engine.get_real_race_replay(track_id, race_id, track_info)
        
        print(f"[TrackParser] Replay data: {len(replay_data.get('lap_progression', []))} laps, {replay_data.get('total_drivers', 0)} drivers")
        
        return replay_data
    
    def _get_track_info(self, track_id: str) -> Optional[Dict]:
        """Get track information by ID."""
        tracks = {
            "barber": {"name": "Barber Motorsports Park", "path": "barber-motorsports-park/barber"},
            "cota": {"name": "Circuit of the Americas", "path": "circuit-of-the-americas/COTA"},
            "indianapolis": {"name": "Indianapolis Motor Speedway", "path": "indianapolis/indianapolis"},
            "road-america": {"name": "Road America", "path": "road-america/road-america/Road America"},
            "sebring": {"name": "Sebring International Raceway", "path": "sebring/sebring/Sebring"},
            "sonoma": {"name": "Sonoma Raceway", "path": "sonoma/Sonoma"},
            "vir": {"name": "Virginia International Raceway", "path": "virginia-international-raceway/virginia-international-raceway/VIR"}
        }
        
        return tracks.get(track_id)


def get_track_parser() -> TrackDataParser:
    """Get global track parser instance."""
    return TrackDataParser()

