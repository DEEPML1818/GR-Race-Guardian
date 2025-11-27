# 💾 Storage System Documentation

## Overview

GR Race Guardian uses a **JSON-based storage system** that provides the same interface as SQLite for easy migration later.

## Current Implementation: JSON Storage

### Location
- **Storage Directory**: `backend-python/storage/`
- **Files**: JSON files for each data type
  - `race_sessions.json` - Race session data
  - `driver_metrics.json` - Driver performance metrics
  - `lap_data.json` - Lap timing data
  - `predictions.json` - ML predictions
  - `simulations.json` - Monte Carlo simulation results

### Benefits
- ✅ **No Dependencies** - Uses only Python standard library (json, threading)
- ✅ **Lightweight** - No database server needed
- ✅ **Easy Migration** - Same interface as SQLite
- ✅ **Human Readable** - JSON files can be inspected directly
- ✅ **Thread-Safe** - Uses locks for concurrent access

### Usage

```python
from database import get_db

# Get storage instance (same interface as SQLite)
db = get_db()

# Create a race session
session_id = db.create_session(circuit="Barber Motorsports Park", race_type="race")

# Save driver metrics
db.save_driver_metrics(session_id, "driver_1", {
    'consistency_index': 0.92,
    'aggression_score': {'aggression_score': 0.65}
})

# Get session metrics
metrics = db.get_session_metrics(session_id)

# Close (no-op for JSON, but keeps interface compatible)
db.close()
```

## Migration to SQLite (Future)

When you're ready to migrate to SQLite:

### Step 1: Update imports

In `backend-python/database/db.py`, change:

```python
# FROM:
from .storage import RaceStorage, get_db

# TO:
from .db_sqlite import RaceDatabase, get_db
```

### Step 2: That's it!

All existing code will work without any changes because the interface is identical!

### Optional: Install SQLAlchemy

```bash
pip install sqlalchemy
```

(Though SQLite is built into Python, SQLAlchemy can provide ORM features if needed)

## Storage Interface

Both JSON and SQLite implementations support:

- `create_session(circuit, date, race_type)` - Create race session
- `save_driver_metrics(session_id, driver_id, metrics)` - Save metrics
- `save_lap_data(session_id, driver_id, lap_number, lap_time, sectors, lap_type, position)` - Save lap data
- `save_prediction(session_id, driver_id, prediction_type, prediction_value, model_path, confidence)` - Save predictions
- `save_simulation(session_id, driver_paces, n_laps, iterations, results)` - Save simulations
- `get_session_metrics(session_id)` - Get metrics
- `get_session_laps(session_id)` - Get lap data
- `get_session_predictions(session_id)` - Get predictions
- `get_sessions(circuit)` - Get all sessions
- `close()` - Close connection

## File Structure

```
backend-python/
  ├── database/
  │   ├── __init__.py        # Package exports
  │   ├── db.py              # Main interface (swappable)
  │   ├── storage.py         # JSON storage implementation
  │   └── db_sqlite.py       # SQLite implementation (optional)
  └── storage/               # JSON files directory
      ├── race_sessions.json
      ├── driver_metrics.json
      ├── lap_data.json
      ├── predictions.json
      └── simulations.json
```

## Data Format

All data is stored as JSON with the same structure:

### Race Session
```json
{
  "id": 1,
  "circuit": "Barber Motorsports Park",
  "date": "2024-01-15T10:00:00",
  "race_type": "race",
  "created_at": "2024-01-15T10:00:00",
  "updated_at": "2024-01-15T10:00:00"
}
```

### Driver Metrics
```json
{
  "id": 1,
  "session_id": 1,
  "driver_id": "driver_1",
  "consistency_index": 0.92,
  "aggression_score": 0.65,
  "sector_strength": {...},
  "pace_stability": {...},
  "fatigue_dropoff": {...},
  "created_at": "2024-01-15T10:00:00"
}
```

## Thread Safety

The JSON storage system uses Python's `threading.Lock` to ensure thread-safe file operations, so it's safe to use in a multi-threaded FastAPI environment.

## Backup

Since data is stored as JSON files, backing up is simple:

```bash
# Backup storage directory
cp -r backend-python/storage/ backup/storage_$(date +%Y%m%d)/
```

## Performance

For typical race data (hundreds to thousands of records), JSON storage is perfectly adequate. If you need to handle millions of records or complex queries, SQLite would be a better choice.

---

**Current Status**: Using JSON storage ✅  
**Migration**: Easy (just change one import) 🔄  
**All code works with both!** 🎉

