"""
JSON-based storage system for GR Race Guardian

Lightweight file-based storage that can be easily replaced with SQLite later.
Uses the same interface as SQLite for easy migration.
"""
import os
import json
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path
import threading


class RaceStorage:
    """
    JSON-based storage manager for race data.
    
    Uses JSON files for persistence. Same interface as SQLite for easy migration.
    """
    
    def __init__(self, storage_dir: str = 'storage'):
        """Initialize storage system."""
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # Storage files
        self.sessions_file = self.storage_dir / 'race_sessions.json'
        self.metrics_file = self.storage_dir / 'driver_metrics.json'
        self.lap_data_file = self.storage_dir / 'lap_data.json'
        self.predictions_file = self.storage_dir / 'predictions.json'
        self.simulations_file = self.storage_dir / 'simulations.json'
        
        # Thread lock for file operations
        self.lock = threading.Lock()
        
        # Initialize storage files
        self._init_storage()
        
        # Auto-increment IDs
        self._session_id = self._get_next_id('sessions')
        self._metrics_id = self._get_next_id('metrics')
        self._lap_data_id = self._get_next_id('lap_data')
        self._predictions_id = self._get_next_id('predictions')
        self._simulations_id = self._get_next_id('simulations')
    
    def _init_storage(self):
        """Initialize storage files if they don't exist."""
        files = {
            self.sessions_file: [],
            self.metrics_file: [],
            self.lap_data_file: [],
            self.predictions_file: [],
            self.simulations_file: []
        }
        
        for file_path, default_data in files.items():
            if not file_path.exists():
                self._write_file(file_path, default_data)
    
    def _read_file(self, file_path: Path) -> List[Dict]:
        """Read JSON file safely."""
        with self.lock:
            try:
                if file_path.exists() and file_path.stat().st_size > 0:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                return []
            except (json.JSONDecodeError, IOError):
                return []
    
    def _write_file(self, file_path: Path, data: List[Dict]):
        """Write JSON file safely."""
        with self.lock:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _get_next_id(self, storage_type: str) -> int:
        """Get next auto-increment ID for a storage type."""
        file_map = {
            'sessions': self.sessions_file,
            'metrics': self.metrics_file,
            'lap_data': self.lap_data_file,
            'predictions': self.predictions_file,
            'simulations': self.simulations_file
        }
        
        file_path = file_map.get(storage_type)
        if not file_path:
            return 1
        
        data = self._read_file(file_path)
        if not data:
            return 1
        
        max_id = max([item.get('id', 0) for item in data], default=0)
        return max_id + 1
    
    def create_session(self, circuit: str, date: Optional[str] = None, race_type: str = 'race') -> int:
        """Create a new race session."""
        if date is None:
            date = datetime.now().isoformat()
        
        session_data = {
            'id': self._session_id,
            'circuit': circuit,
            'date': date,
            'race_type': race_type,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        sessions = self._read_file(self.sessions_file)
        sessions.append(session_data)
        self._write_file(self.sessions_file, sessions)
        
        session_id = self._session_id
        self._session_id += 1
        
        return session_id
    
    def save_driver_metrics(self, session_id: int, driver_id: str, metrics: Dict):
        """Save driver metrics to storage."""
        metrics_data = {
            'id': self._metrics_id,
            'session_id': session_id,
            'driver_id': driver_id,
            'consistency_index': metrics.get('consistency_index'),
            'aggression_score': metrics.get('aggression_score', {}).get('aggression_score'),
            'sector_strength': metrics.get('sector_strength', {}),
            'pace_stability': metrics.get('pace_stability', {}),
            'fatigue_dropoff': metrics.get('fatigue_dropoff', {}),
            'created_at': datetime.now().isoformat()
        }
        
        all_metrics = self._read_file(self.metrics_file)
        all_metrics.append(metrics_data)
        self._write_file(self.metrics_file, all_metrics)
        
        self._metrics_id += 1
    
    def save_lap_data(self, session_id: int, driver_id: str, lap_number: int,
                     lap_time: float, sectors: Dict, lap_type: str, position: int):
        """Save lap data to storage."""
        lap_data = {
            'id': self._lap_data_id,
            'session_id': session_id,
            'driver_id': driver_id,
            'lap_number': lap_number,
            'lap_time': lap_time,
            'sector_1': sectors.get('S1'),
            'sector_2': sectors.get('S2'),
            'sector_3': sectors.get('S3'),
            'lap_type': lap_type,
            'position': position,
            'created_at': datetime.now().isoformat()
        }
        
        all_laps = self._read_file(self.lap_data_file)
        all_laps.append(lap_data)
        self._write_file(self.lap_data_file, all_laps)
        
        self._lap_data_id += 1
    
    def save_prediction(self, session_id: int, driver_id: str, prediction_type: str,
                       prediction_value: float, model_path: str, confidence: Optional[float] = None):
        """Save prediction to storage."""
        prediction_data = {
            'id': self._predictions_id,
            'session_id': session_id,
            'driver_id': driver_id,
            'prediction_type': prediction_type,
            'prediction_value': prediction_value,
            'model_path': model_path,
            'confidence': confidence,
            'created_at': datetime.now().isoformat()
        }
        
        all_predictions = self._read_file(self.predictions_file)
        all_predictions.append(prediction_data)
        self._write_file(self.predictions_file, all_predictions)
        
        self._predictions_id += 1
    
    def save_simulation(self, session_id: int, driver_paces: Dict, n_laps: int,
                       iterations: int, results: Dict) -> int:
        """Save Monte Carlo simulation results."""
        simulation_data = {
            'id': self._simulations_id,
            'session_id': session_id,
            'driver_paces': driver_paces,
            'n_laps': n_laps,
            'iterations': iterations,
            'results': results,
            'created_at': datetime.now().isoformat()
        }
        
        all_simulations = self._read_file(self.simulations_file)
        all_simulations.append(simulation_data)
        self._write_file(self.simulations_file, all_simulations)
        
        sim_id = self._simulations_id
        self._simulations_id += 1
        
        return sim_id
    
    def get_session_metrics(self, session_id: int) -> List[Dict]:
        """Get all driver metrics for a session."""
        all_metrics = self._read_file(self.metrics_file)
        return [m for m in all_metrics if m.get('session_id') == session_id]
    
    def get_session_laps(self, session_id: int) -> List[Dict]:
        """Get all lap data for a session."""
        all_laps = self._read_file(self.lap_data_file)
        return [l for l in all_laps if l.get('session_id') == session_id]
    
    def get_session_predictions(self, session_id: int) -> List[Dict]:
        """Get all predictions for a session."""
        all_predictions = self._read_file(self.predictions_file)
        return [p for p in all_predictions if p.get('session_id') == session_id]
    
    def get_sessions(self, circuit: Optional[str] = None) -> List[Dict]:
        """Get all race sessions, optionally filtered by circuit."""
        all_sessions = self._read_file(self.sessions_file)
        if circuit:
            return [s for s in all_sessions if s.get('circuit') == circuit]
        return all_sessions
    
    def close(self):
        """Close storage (no-op for JSON files, but keeps interface compatible)."""
        pass
    
    def clear_all(self):
        """Clear all storage (for testing)."""
        files = [
            self.sessions_file,
            self.metrics_file,
            self.lap_data_file,
            self.predictions_file,
            self.simulations_file
        ]
        for file_path in files:
            self._write_file(file_path, [])


# Alias for backward compatibility - same interface as SQLite version
RaceDatabase = RaceStorage


# Global storage instance
_storage_instance = None

def get_db(storage_dir: str = 'storage') -> RaceStorage:
    """Get or create storage instance."""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = RaceStorage(storage_dir)
    return _storage_instance


# For easy migration to SQLite later, just change:
# from database.storage import get_db  -> from database.db import get_db
# The interface is the same!

