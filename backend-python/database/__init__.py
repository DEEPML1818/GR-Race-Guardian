"""
Database package for GR Race Guardian

Provides data persistence with interchangeable backends.
"""
from .storage import RaceStorage, get_db

# Export for backward compatibility
RaceDatabase = RaceStorage

__all__ = ['RaceDatabase', 'RaceStorage', 'get_db']

