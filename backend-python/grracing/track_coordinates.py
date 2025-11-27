"""
Track Coordinates

Defines coordinate systems and layouts for all supported tracks.
These coordinates are normalized (0-1) for SVG rendering.
"""

from typing import Dict, List, Tuple


class TrackCoordinates:
    """
    Track coordinate definitions for visualization.
    """
    
    def __init__(self):
        self.tracks = {
            "barber": {
                "name": "Barber Motorsports Park",
                "length": 2.38,  # miles
                "turns": 17,
                "coordinates": self._barber_coordinates()
            },
            "cota": {
                "name": "Circuit of the Americas",
                "length": 3.427,  # miles
                "turns": 20,
                "coordinates": self._cota_coordinates()
            },
            "indianapolis": {
                "name": "Indianapolis Motor Speedway",
                "length": 2.439,  # miles (road course)
                "turns": 14,
                "coordinates": self._indianapolis_coordinates()
            },
            "road-america": {
                "name": "Road America",
                "length": 4.048,  # miles
                "turns": 14,
                "coordinates": self._road_america_coordinates()
            },
            "sebring": {
                "name": "Sebring International Raceway",
                "length": 3.74,  # miles
                "turns": 17,
                "coordinates": self._sebring_coordinates()
            },
            "sonoma": {
                "name": "Sonoma Raceway",
                "length": 2.52,  # miles
                "turns": 12,
                "coordinates": self._sonoma_coordinates()
            },
            "vir": {
                "name": "Virginia International Raceway",
                "length": 3.27,  # miles (full course)
                "turns": 17,
                "coordinates": self._vir_coordinates()
            }
        }
    
    def get_track_coordinates(self, track_id: str) -> Dict:
        """Get coordinates for a specific track."""
        return self.tracks.get(track_id, {})
    
    def get_all_tracks(self) -> Dict:
        """Get all track definitions."""
        return self.tracks
    
    def _barber_coordinates(self) -> List[Dict]:
        """
        Barber Motorsports Park - 2.38 miles, 17 turns
        Technical park circuit with elevation changes
        """
        return [
            {"x": 0.15, "y": 0.65, "type": "start_finish", "name": "Start/Finish"},
            {"x": 0.18, "y": 0.63, "type": "straight"},
            {"x": 0.22, "y": 0.60, "type": "straight"},
            {"x": 0.28, "y": 0.55, "type": "turn", "name": "Turn 1"},
            {"x": 0.32, "y": 0.48, "type": "turn", "name": "Turn 2"},
            {"x": 0.35, "y": 0.42, "type": "turn", "name": "Turn 3"},
            {"x": 0.38, "y": 0.36, "type": "straight"},
            {"x": 0.42, "y": 0.30, "type": "turn", "name": "Turn 4"},
            {"x": 0.48, "y": 0.25, "type": "turn", "name": "Turn 5"},
            {"x": 0.55, "y": 0.22, "type": "straight"},
            {"x": 0.62, "y": 0.20, "type": "turn", "name": "Turn 6"},
            {"x": 0.68, "y": 0.22, "type": "turn", "name": "Turn 7"},
            {"x": 0.73, "y": 0.26, "type": "straight"},
            {"x": 0.78, "y": 0.32, "type": "turn", "name": "Turn 8"},
            {"x": 0.82, "y": 0.40, "type": "turn", "name": "Turn 9"},
            {"x": 0.84, "y": 0.48, "type": "straight"},
            {"x": 0.85, "y": 0.56, "type": "turn", "name": "Turn 10"},
            {"x": 0.83, "y": 0.63, "type": "turn", "name": "Turn 11"},
            {"x": 0.78, "y": 0.68, "type": "straight"},
            {"x": 0.72, "y": 0.72, "type": "turn", "name": "Turn 12"},
            {"x": 0.65, "y": 0.75, "type": "turn", "name": "Turn 13"},
            {"x": 0.58, "y": 0.76, "type": "straight"},
            {"x": 0.50, "y": 0.75, "type": "turn", "name": "Turn 14"},
            {"x": 0.43, "y": 0.72, "type": "turn", "name": "Turn 15"},
            {"x": 0.36, "y": 0.68, "type": "straight"},
            {"x": 0.28, "y": 0.66, "type": "turn", "name": "Turn 16"},
            {"x": 0.22, "y": 0.65, "type": "turn", "name": "Turn 17"},
            {"x": 0.15, "y": 0.65, "type": "straight", "name": "Final Straight"}
        ]
    
    def _cota_coordinates(self) -> List[Dict]:
        """
        Circuit of the Americas - 3.427 miles, 20 turns
        Modern F1-style track with dramatic elevation changes
        """
        return [
            {"x": 0.50, "y": 0.85, "type": "start_finish", "name": "Start/Finish"},
            {"x": 0.48, "y": 0.78, "type": "straight"},
            {"x": 0.45, "y": 0.70, "type": "straight"},
            {"x": 0.40, "y": 0.60, "type": "turn", "name": "Turn 1"},
            {"x": 0.35, "y": 0.52, "type": "turn", "name": "Turn 2"},
            {"x": 0.32, "y": 0.45, "type": "turn", "name": "Turn 3"},
            {"x": 0.30, "y": 0.38, "type": "turn", "name": "Turn 4"},
            {"x": 0.28, "y": 0.32, "type": "turn", "name": "Turn 5"},
            {"x": 0.27, "y": 0.26, "type": "turn", "name": "Turn 6"},
            {"x": 0.28, "y": 0.20, "type": "straight"},
            {"x": 0.32, "y": 0.15, "type": "turn", "name": "Turn 7"},
            {"x": 0.38, "y": 0.12, "type": "turn", "name": "Turn 8"},
            {"x": 0.45, "y": 0.10, "type": "turn", "name": "Turn 9"},
            {"x": 0.52, "y": 0.11, "type": "turn", "name": "Turn 10"},
            {"x": 0.58, "y": 0.14, "type": "turn", "name": "Turn 11"},
            {"x": 0.65, "y": 0.18, "type": "straight"},
            {"x": 0.72, "y": 0.24, "type": "turn", "name": "Turn 12"},
            {"x": 0.77, "y": 0.32, "type": "turn", "name": "Turn 13"},
            {"x": 0.80, "y": 0.40, "type": "turn", "name": "Turn 14"},
            {"x": 0.81, "y": 0.48, "type": "turn", "name": "Turn 15"},
            {"x": 0.78, "y": 0.55, "type": "straight"},
            {"x": 0.73, "y": 0.60, "type": "turn", "name": "Turn 16"},
            {"x": 0.68, "y": 0.64, "type": "turn", "name": "Turn 17"},
            {"x": 0.63, "y": 0.67, "type": "turn", "name": "Turn 18"},
            {"x": 0.58, "y": 0.70, "type": "turn", "name": "Turn 19"},
            {"x": 0.54, "y": 0.75, "type": "turn", "name": "Turn 20"},
            {"x": 0.52, "y": 0.80, "type": "straight"},
            {"x": 0.50, "y": 0.85, "type": "straight", "name": "Final Straight"}
        ]
    
    def _indianapolis_coordinates(self) -> List[Dict]:
        """
        Indianapolis Motor Speedway Road Course - 2.439 miles, 14 turns
        Combination of infield road course and oval sections
        """
        return [
            {"x": 0.20, "y": 0.75, "type": "start_finish", "name": "Start/Finish"},
            {"x": 0.25, "y": 0.72, "type": "straight"},
            {"x": 0.32, "y": 0.68, "type": "straight"},
            {"x": 0.40, "y": 0.65, "type": "turn", "name": "Turn 1"},
            {"x": 0.48, "y": 0.60, "type": "straight"},
            {"x": 0.55, "y": 0.54, "type": "turn", "name": "Turn 2"},
            {"x": 0.60, "y": 0.47, "type": "turn", "name": "Turn 3"},
            {"x": 0.63, "y": 0.40, "type": "straight"},
            {"x": 0.65, "y": 0.32, "type": "turn", "name": "Turn 4"},
            {"x": 0.65, "y": 0.25, "type": "turn", "name": "Turn 5"},
            {"x": 0.62, "y": 0.18, "type": "straight"},
            {"x": 0.56, "y": 0.14, "type": "turn", "name": "Turn 6"},
            {"x": 0.48, "y": 0.12, "type": "turn", "name": "Turn 7"},
            {"x": 0.40, "y": 0.13, "type": "straight"},
            {"x": 0.32, "y": 0.16, "type": "turn", "name": "Turn 8"},
            {"x": 0.25, "y": 0.22, "type": "turn", "name": "Turn 9"},
            {"x": 0.20, "y": 0.30, "type": "straight"},
            {"x": 0.16, "y": 0.38, "type": "turn", "name": "Turn 10"},
            {"x": 0.14, "y": 0.46, "type": "turn", "name": "Turn 11"},
            {"x": 0.13, "y": 0.54, "type": "straight"},
            {"x": 0.14, "y": 0.62, "type": "turn", "name": "Turn 12"},
            {"x": 0.16, "y": 0.69, "type": "turn", "name": "Turn 13"},
            {"x": 0.18, "y": 0.73, "type": "turn", "name": "Turn 14"},
            {"x": 0.20, "y": 0.75, "type": "straight", "name": "Final Straight"}
        ]
    
    def _road_america_coordinates(self) -> List[Dict]:
        """
        Road America - 4.048 miles, 14 turns
        Long, fast natural terrain road course
        """
        return [
            {"x": 0.25, "y": 0.80, "type": "start_finish", "name": "Start/Finish"},
            {"x": 0.30, "y": 0.75, "type": "straight"},
            {"x": 0.38, "y": 0.68, "type": "straight"},
            {"x": 0.45, "y": 0.60, "type": "turn", "name": "Turn 1"},
            {"x": 0.50, "y": 0.52, "type": "turn", "name": "Turn 2"},
            {"x": 0.54, "y": 0.44, "type": "turn", "name": "Turn 3"},
            {"x": 0.58, "y": 0.36, "type": "straight"},
            {"x": 0.62, "y": 0.28, "type": "turn", "name": "Turn 4"},
            {"x": 0.67, "y": 0.22, "type": "turn", "name": "Turn 5"},
            {"x": 0.73, "y": 0.18, "type": "straight"},
            {"x": 0.80, "y": 0.16, "type": "turn", "name": "Turn 6"},
            {"x": 0.85, "y": 0.20, "type": "turn", "name": "Turn 7"},
            {"x": 0.88, "y": 0.28, "type": "straight"},
            {"x": 0.88, "y": 0.36, "type": "turn", "name": "Turn 8"},
            {"x": 0.85, "y": 0.44, "type": "turn", "name": "Turn 9"},
            {"x": 0.80, "y": 0.50, "type": "turn", "name": "Turn 10"},
            {"x": 0.73, "y": 0.55, "type": "straight"},
            {"x": 0.65, "y": 0.60, "type": "turn", "name": "Turn 11"},
            {"x": 0.56, "y": 0.65, "type": "turn", "name": "Turn 12"},
            {"x": 0.46, "y": 0.70, "type": "straight"},
            {"x": 0.36, "y": 0.74, "type": "turn", "name": "Turn 13"},
            {"x": 0.28, "y": 0.78, "type": "turn", "name": "Turn 14"},
            {"x": 0.25, "y": 0.80, "type": "straight", "name": "Final Straight"}
        ]
    
    def _sebring_coordinates(self) -> List[Dict]:
        """
        Sebring International Raceway - 3.74 miles, 17 turns
        Historic endurance racing track
        """
        return [
            {"x": 0.1, "y": 0.5, "type": "start_finish", "name": "Start/Finish"},
            {"x": 0.2, "y": 0.4, "type": "straight", "name": "Main Straight"},
            {"x": 0.35, "y": 0.3, "type": "turn", "name": "Turn 1", "angle": 90},
            {"x": 0.5, "y": 0.25, "type": "straight", "name": "Back Straight"},
            {"x": 0.65, "y": 0.3, "type": "turn", "name": "Turn 2", "angle": 90},
            {"x": 0.8, "y": 0.4, "type": "straight", "name": "Section 1"},
            {"x": 0.85, "y": 0.5, "type": "turn", "name": "Turn 3", "angle": 90},
            {"x": 0.8, "y": 0.6, "type": "straight", "name": "Section 2"},
            {"x": 0.65, "y": 0.7, "type": "turn", "name": "Turn 4", "angle": 90},
            {"x": 0.5, "y": 0.75, "type": "straight", "name": "Section 3"},
            {"x": 0.35, "y": 0.7, "type": "turn", "name": "Turn 5", "angle": 90},
            {"x": 0.2, "y": 0.6, "type": "straight", "name": "Section 4"},
            {"x": 0.1, "y": 0.5, "type": "straight", "name": "Final Straight"}
        ]
    
    def _sonoma_coordinates(self) -> List[Dict]:
        """
        Sonoma Raceway - 2.52 miles, 12 turns
        Technical track with significant elevation changes
        """
        return [
            {"x": 0.30, "y": 0.75, "type": "start_finish", "name": "Start/Finish"},
            {"x": 0.35, "y": 0.70, "type": "straight"},
            {"x": 0.42, "y": 0.63, "type": "straight"},
            {"x": 0.50, "y": 0.55, "type": "turn", "name": "Turn 1"},
            {"x": 0.56, "y": 0.48, "type": "turn", "name": "Turn 2"},
            {"x": 0.60, "y": 0.40, "type": "straight"},
            {"x": 0.63, "y": 0.32, "type": "turn", "name": "Turn 3"},
            {"x": 0.65, "y": 0.24, "type": "turn", "name": "Turn 3A"},
            {"x": 0.68, "y": 0.18, "type": "straight"},
            {"x": 0.73, "y": 0.14, "type": "turn", "name": "Turn 4"},
            {"x": 0.78, "y": 0.12, "type": "turn", "name": "Turn 4A"},
            {"x": 0.83, "y": 0.15, "type": "straight"},
            {"x": 0.86, "y": 0.22, "type": "turn", "name": "Turn 5"},
            {"x": 0.87, "y": 0.30, "type": "turn", "name": "Turn 6"},
            {"x": 0.85, "y": 0.38, "type": "straight"},
            {"x": 0.80, "y": 0.45, "type": "turn", "name": "Turn 7"},
            {"x": 0.73, "y": 0.52, "type": "turn", "name": "Turn 8"},
            {"x": 0.65, "y": 0.58, "type": "straight"},
            {"x": 0.56, "y": 0.63, "type": "turn", "name": "Turn 9"},
            {"x": 0.47, "y": 0.68, "type": "turn", "name": "Turn 10"},
            {"x": 0.38, "y": 0.72, "type": "turn", "name": "Turn 11"},
            {"x": 0.32, "y": 0.74, "type": "straight", "name": "Final Straight"}
        ]
    
    def _vir_coordinates(self) -> List[Dict]:
        """
        Virginia International Raceway - 3.27 miles, 17 turns
        Fast, flowing track with natural terrain
        """
        return [
            {"x": 0.20, "y": 0.70, "type": "start_finish", "name": "Start/Finish"},
            {"x": 0.25, "y": 0.65, "type": "straight"},
            {"x": 0.32, "y": 0.58, "type": "straight"},
            {"x": 0.40, "y": 0.50, "type": "turn", "name": "Turn 1"},
            {"x": 0.46, "y": 0.42, "type": "turn", "name": "Turn 2"},
            {"x": 0.52, "y": 0.35, "type": "straight"},
            {"x": 0.58, "y": 0.28, "type": "turn", "name": "Turn 3"},
            {"x": 0.64, "y": 0.22, "type": "turn", "name": "Turn 4"},
            {"x": 0.70, "y": 0.18, "type": "straight"},
            {"x": 0.76, "y": 0.16, "type": "turn", "name": "Turn 5"},
            {"x": 0.82, "y": 0.18, "type": "turn", "name": "Turn 6"},
            {"x": 0.86, "y": 0.24, "type": "straight"},
            {"x": 0.88, "y": 0.32, "type": "turn", "name": "Turn 7"},
            {"x": 0.88, "y": 0.40, "type": "turn", "name": "Turn 8"},
            {"x": 0.85, "y": 0.48, "type": "straight"},
            {"x": 0.80, "y": 0.55, "type": "turn", "name": "Turn 9"},
            {"x": 0.74, "y": 0.60, "type": "turn", "name": "Turn 10"},
            {"x": 0.67, "y": 0.64, "type": "straight"},
            {"x": 0.59, "y": 0.67, "type": "turn", "name": "Turn 11"},
            {"x": 0.51, "y": 0.70, "type": "turn", "name": "Turn 12"},
            {"x": 0.43, "y": 0.72, "type": "straight"},
            {"x": 0.35, "y": 0.73, "type": "turn", "name": "Turn 13"},
            {"x": 0.28, "y": 0.72, "type": "turn", "name": "Turn 14"},
            {"x": 0.22, "y": 0.70, "type": "straight", "name": "Final Straight"}
        ]
    
    def get_track_svg_path(self, track_id: str) -> str:
        """
        Generate SVG path for track visualization.
        Returns path data for SVG <path> element.
        Creates a smooth closed loop track from coordinate points.
        """
        coords = self.get_track_coordinates(track_id)
        if not coords or "coordinates" not in coords:
            return ""
        
        points = coords["coordinates"]
        if not points or len(points) < 3:
            return ""
        
        path_data = []
        
        # Scale coordinates to SVG viewBox (0-1000)
        scaled_points = [(p["x"] * 1000, p["y"] * 1000) for p in points]
        
        # Start with the midpoint between the last and first point to ensure a smooth loop
        # or just start at the first point.
        # Let's use a standard Catmull-Rom or just the quadratic bezier approach which works well for tracks.
        
        # Method: Draw from midpoint to midpoint using the point as control
        
        # 1. Calculate all midpoints
        # We need a closed loop, so append the first couple of points to the end
        p = scaled_points
        # Add first two points to end to close the loop smoothly
        p_loop = p + [p[0], p[1]]
        
        # Start at midpoint of first segment
        mx0 = (p_loop[0][0] + p_loop[1][0]) / 2
        my0 = (p_loop[0][1] + p_loop[1][1]) / 2
        
        path_data.append(f"M {mx0} {my0}")
        
        # Loop through points
        for i in range(1, len(p) + 1):
            # Current point (control point)
            p1 = p_loop[i]
            # Next point
            p2 = p_loop[i+1]
            
            # Midpoint (destination)
            mx = (p1[0] + p2[0]) / 2
            my = (p1[1] + p2[1]) / 2
            
            # Curve from previous midpoint to this midpoint, using p1 as control
            path_data.append(f"Q {p1[0]} {p1[1]} {mx} {my}")
            
        return " ".join(path_data)


def get_track_coordinates() -> TrackCoordinates:
    """Get global track coordinates instance."""
    return TrackCoordinates()

