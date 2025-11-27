"""
GPS Coordinates for Race Tracks

Simple, working GPS coordinates for OpenStreetMap visualization.
"""

from typing import Dict, List, Tuple


class GPSTrackCoordinates:
    """Real GPS coordinates for race tracks."""
    
    def __init__(self):
        self.tracks = {
            "barber": {
                "name": "Barber Motorsports Park",
                "center": [33.5492, -86.3789],
                "zoom": 15,
                "bounds": [[33.5520, -86.3820], [33.5480, -86.3760]]
            },
            "cota": {
                "name": "Circuit of the Americas",
                "center": [30.1328, -97.6411],
                "zoom": 14,
                "bounds": [[30.1380, -97.6480], [30.1280, -97.6340]]
            },
            "indianapolis": {
                "name": "Indianapolis Motor Speedway",
                "center": [39.7950, -86.2350],
                "zoom": 15,
                "bounds": [[39.8000, -86.2400], [39.7900, -86.2300]]
            },
            "road-america": {
                "name": "Road America",
                "center": [43.8014, -87.9897],
                "zoom": 14,
                "bounds": [[43.8100, -88.0000], [43.7930, -87.9800]]
            },
            "sebring": {
                "name": "Sebring International Raceway",
                "center": [27.4515, -81.3485],
                "zoom": 14,
                "bounds": [[27.4580, -81.3550], [27.4450, -81.3420]]
            },
            "sonoma": {
                "name": "Sonoma Raceway",
                "center": [38.1614, -122.4544],
                "zoom": 15,
                "bounds": [[38.1650, -122.4580], [38.1580, -122.4510]]
            },
            "vir": {
                "name": "Virginia International Raceway",
                "center": [36.5875, -79.2025],
                "zoom": 14,
                "bounds": [[36.5950, -79.2100], [36.5800, -79.1950]]
            },
            "laguna-seca": {
                "name": "WeatherTech Raceway Laguna Seca",
                "center": [36.5847, -121.7539],
                "zoom": 15,
                "bounds": [[36.5880, -121.7580], [36.5810, -121.7500]]
            }
        }
    
    def get_track_gps(self, track_id: str) -> Dict:
        """Get GPS coordinates for a specific track."""
        return self.tracks.get(track_id, {})
    
    def get_all_tracks(self) -> Dict:
        """Get all track GPS definitions."""
        return self.tracks
    
    def normalize_to_gps(self, track_id: str, normalized_coords: List[Dict]) -> List[Tuple[float, float]]:
        """
        Convert normalized coordinates (0-1) to GPS coordinates.
        Simply maps normalized coordinates to GPS bounds - no fake track paths.
        """
        track_gps = self.get_track_gps(track_id)
        if not track_gps or "bounds" not in track_gps:
            return []
        
        bounds = track_gps["bounds"]
        lat_min, lon_min = bounds[1]
        lat_max, lon_max = bounds[0]
        
        gps_coords = []
        for coord in normalized_coords:
            lat = lat_max - (coord["y"] * (lat_max - lat_min))
            lon = lon_min + (coord["x"] * (lon_max - lon_min))
            gps_coords.append((lat, lon))
        
        return gps_coords


def get_gps_track_coordinates() -> GPSTrackCoordinates:
    """Get global GPS track coordinates instance."""
    return GPSTrackCoordinates()
