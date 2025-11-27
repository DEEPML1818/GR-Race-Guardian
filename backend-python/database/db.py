"""
Database/storage abstraction for GR Race Guardian

This module provides a unified interface for data persistence.
Currently uses JSON-based storage, but can be easily replaced with SQLite.

To migrate to SQLite:
1. Uncomment the SQLite import below
2. Comment out the JSON storage import
3. All existing code will work without changes!
"""
# Option 1: JSON-based storage (current - lightweight, no dependencies)
from .storage import RaceStorage, get_db

# Option 2: SQLite storage (uncomment to use SQLite instead)
# from .db_sqlite import RaceDatabase, get_db

# Export the storage class (same interface regardless of backend)
RaceDatabase = RaceStorage

__all__ = ['RaceDatabase', 'RaceStorage', 'get_db']
