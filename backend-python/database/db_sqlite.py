"""
SQLite Database Storage (Optional - for future migration)

This module provides SQLite-based storage with the same interface
as the JSON storage system for easy swapping.

To use SQLite instead of JSON storage:
1. In database/db.py, uncomment: from .db_sqlite import RaceDatabase, get_db
2. Comment out: from .storage import RaceStorage, get_db
3. Install: pip install sqlalchemy (if not already installed)

All existing code will work without any changes!
"""
import os
import sqlite3
from datetime import datetime
from typing import Optional, Dict, List
import json


class RaceDatabase:
    """SQLite database manager for race data."""
    
    def __init__(self, db_path: str = 'race_data.db'):
        """Initialize database connection."""
        self.db_path = db_path
        self.conn = None
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        
        # Race sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS race_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                circuit TEXT NOT NULL,
                date TEXT NOT NULL,
                race_type TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Driver metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS driver_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                driver_id TEXT NOT NULL,
                consistency_index REAL,
                aggression_score REAL,
                sector_strength TEXT,
                pace_stability TEXT,
                fatigue_dropoff TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES race_sessions(id)
            )
        ''')
        
        # Lap data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lap_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                driver_id TEXT NOT NULL,
                lap_number INTEGER,
                lap_time REAL,
                sector_1 REAL,
                sector_2 REAL,
                sector_3 REAL,
                lap_type TEXT,
                position INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES race_sessions(id)
            )
        ''')
        
        # Predictions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                driver_id TEXT NOT NULL,
                prediction_type TEXT,
                prediction_value REAL,
                model_path TEXT,
                confidence REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES race_sessions(id)
            )
        ''')
        
        # Monte Carlo simulations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS simulations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                driver_paces TEXT,
                n_laps INTEGER,
                iterations INTEGER,
                results TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES race_sessions(id)
            )
        ''')
        
        self.conn.commit()
    
    def create_session(self, circuit: str, date: Optional[str] = None, race_type: str = 'race') -> int:
        """Create a new race session."""
        if date is None:
            date = datetime.now().isoformat()
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO race_sessions (circuit, date, race_type)
            VALUES (?, ?, ?)
        ''', (circuit, date, race_type))
        self.conn.commit()
        return cursor.lastrowid
    
    def save_driver_metrics(self, session_id: int, driver_id: str, metrics: Dict):
        """Save driver metrics to database."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO driver_metrics 
            (session_id, driver_id, consistency_index, aggression_score, sector_strength, pace_stability, fatigue_dropoff)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            driver_id,
            metrics.get('consistency_index'),
            metrics.get('aggression_score', {}).get('aggression_score'),
            json.dumps(metrics.get('sector_strength', {})),
            json.dumps(metrics.get('pace_stability', {})),
            json.dumps(metrics.get('fatigue_dropoff', {}))
        ))
        self.conn.commit()
    
    def save_lap_data(self, session_id: int, driver_id: str, lap_number: int,
                     lap_time: float, sectors: Dict, lap_type: str, position: int):
        """Save lap data to database."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO lap_data 
            (session_id, driver_id, lap_number, lap_time, sector_1, sector_2, sector_3, lap_type, position)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id, driver_id, lap_number, lap_time,
            sectors.get('S1'), sectors.get('S2'), sectors.get('S3'),
            lap_type, position
        ))
        self.conn.commit()
    
    def save_prediction(self, session_id: int, driver_id: str, prediction_type: str,
                       prediction_value: float, model_path: str, confidence: Optional[float] = None):
        """Save prediction to database."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO predictions 
            (session_id, driver_id, prediction_type, prediction_value, model_path, confidence)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, driver_id, prediction_type, prediction_value, model_path, confidence))
        self.conn.commit()
    
    def save_simulation(self, session_id: int, driver_paces: Dict, n_laps: int,
                       iterations: int, results: Dict) -> int:
        """Save Monte Carlo simulation results."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO simulations 
            (session_id, driver_paces, n_laps, iterations, results)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            session_id,
            json.dumps(driver_paces),
            n_laps,
            iterations,
            json.dumps(results)
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_session_metrics(self, session_id: int) -> List[Dict]:
        """Get all driver metrics for a session."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM driver_metrics WHERE session_id = ?
        ''', (session_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_session_laps(self, session_id: int) -> List[Dict]:
        """Get all lap data for a session."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM lap_data WHERE session_id = ?', (session_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_session_predictions(self, session_id: int) -> List[Dict]:
        """Get all predictions for a session."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM predictions WHERE session_id = ?', (session_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_sessions(self, circuit: Optional[str] = None) -> List[Dict]:
        """Get all race sessions, optionally filtered by circuit."""
        cursor = self.conn.cursor()
        if circuit:
            cursor.execute('SELECT * FROM race_sessions WHERE circuit = ?', (circuit,))
        else:
            cursor.execute('SELECT * FROM race_sessions')
        return [dict(row) for row in cursor.fetchall()]
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


# Global database instance
_db_instance = None

def get_db(db_path: str = 'race_data.db') -> RaceDatabase:
    """Get or create database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = RaceDatabase(db_path)
    return _db_instance

