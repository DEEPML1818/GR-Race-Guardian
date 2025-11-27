"""
Track Map Backend Logic

Provides track visualization data including:
- Track coordinate system
- Driver positions projection
- Traffic density calculation
- Pit rejoin ghost-driver prediction
- Heatmap generation
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict

from .pit_rejoin import PitRejoinSimulator
from .traffic import TrafficDensityModel


class TrackMapEngine:
    """
    Track map engine for visualizing race positions and traffic.
    """
    
    def __init__(self):
        self.pit_rejoin_sim = PitRejoinSimulator()
        self.traffic_model = TrafficDensityModel()
        
        # Track coordinate system (normalized 0-1 for each sector)
        # This represents a generic track layout
        self.track_coordinates = {
            "S1": {"start": 0.0, "end": 0.33, "type": "straight"},
            "S2": {"start": 0.33, "end": 0.67, "type": "technical"},
            "S3": {"start": 0.67, "end": 1.0, "type": "mixed"}
        }
    
    def get_track_coordinates(
        self,
        track_name: Optional[str] = None
    ) -> Dict:
        """
        Get track coordinate system for visualization.
        
        Returns normalized coordinates (0-1) for each sector.
        """
        # In production, this would load track-specific coordinates
        # For now, return generic 3-sector layout
        
        coordinates = []
        for sector, info in self.track_coordinates.items():
            coordinates.append({
                "sector": sector,
                "start": info["start"],
                "end": info["end"],
                "type": info["type"],
                "length_ratio": info["end"] - info["start"]
            })
        
        return {
            "track_name": track_name or "generic",
            "sectors": coordinates,
            "total_length": 1.0,
            "coordinate_system": "normalized_0_1",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def project_driver_positions(
        self,
        drivers: List[Dict],
        current_lap: int,
        sector: Optional[str] = None
    ) -> Dict:
        """
        Project driver positions onto track coordinate system.
        
        Returns:
        - Driver positions in normalized coordinates
        - Sector assignments
        - Relative positions
        """
        if not drivers:
            return {"drivers": [], "timestamp": datetime.utcnow().isoformat() + "Z"}
        
        projected_drivers = []
        
        for driver in drivers:
            driver_id = driver.get("id", "unknown")
            position = driver.get("position", 1)
            driver_sector = driver.get("sector", sector or "S1")
            lap_time = driver.get("lapTime", driver.get("lap_time", 95.0))
            
            # Calculate position within sector
            sector_info = self.track_coordinates.get(driver_sector, self.track_coordinates["S1"])
            sector_start = sector_info["start"]
            sector_end = sector_info["end"]
            
            # Position within sector (0-1 within that sector)
            # Higher position = further ahead in sector
            position_in_sector = 1.0 - ((position - 1) / max(len(drivers), 1)) * 0.3
            
            # Global track position (0-1 across entire track)
            global_position = sector_start + (sector_end - sector_start) * position_in_sector
            
            projected_drivers.append({
                "driver_id": driver_id,
                "position": position,
                "sector": driver_sector,
                "coordinates": {
                    "global": float(global_position),
                    "sector_local": float(position_in_sector),
                    "sector_start": sector_start,
                    "sector_end": sector_end
                },
                "lap_time": float(lap_time),
                "current_lap": current_lap
            })
        
        # Sort by global position
        projected_drivers.sort(key=lambda x: x["coordinates"]["global"])
        
        return {
            "drivers": projected_drivers,
            "total_drivers": len(drivers),
            "current_lap": current_lap,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def calculate_traffic_density(
        self,
        drivers: List[Dict],
        sector: Optional[str] = None
    ) -> Dict:
        """
        Calculate enhanced traffic density with detailed metrics.
        
        Returns:
        - Density per sector
        - Cars per sector
        - Proximity metrics
        - Time gaps
        """
        if not drivers:
            return {
                "density": {"S1": 0.0, "S2": 0.0, "S3": 0.0},
                "cars_per_sector": {"S1": 0, "S2": 0, "S3": 0},
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        # Count cars per sector
        cars_per_sector = defaultdict(int)
        sector_drivers = defaultdict(list)
        
        for driver in drivers:
            driver_sector = driver.get("sector", sector or "S1")
            cars_per_sector[driver_sector] += 1
            sector_drivers[driver_sector].append(driver)
        
        # Calculate density per sector
        total_drivers = len(drivers)
        density = {}
        proximity_metrics = {}
        
        for sec in ["S1", "S2", "S3"]:
            cars_in_sector = cars_per_sector[sec]
            
            # Basic density (cars / total)
            base_density = cars_in_sector / max(total_drivers, 1)
            
            # Proximity factor (closer positions = higher density)
            if cars_in_sector > 1:
                positions = [d.get("position", 0) for d in sector_drivers[sec]]
                position_spread = max(positions) - min(positions) if positions else 0
                proximity_factor = 1.0 / (1 + position_spread / 5)
                base_density *= (1 + proximity_factor)
            
            density[sec] = min(1.0, base_density)
            
            # Calculate average time gap in sector
            if len(sector_drivers[sec]) > 1:
                lap_times = [d.get("lapTime", d.get("lap_time", 95.0)) for d in sector_drivers[sec]]
                avg_gap = np.mean([abs(lap_times[i] - lap_times[i+1]) for i in range(len(lap_times)-1)]) if len(lap_times) > 1 else 0.0
            else:
                avg_gap = 0.0
            
            proximity_metrics[sec] = {
                "cars": cars_in_sector,
                "avg_gap": float(avg_gap),
                "position_spread": max(positions) - min(positions) if len(sector_drivers[sec]) > 1 else 0
            }
        
        return {
            "density": density,
            "cars_per_sector": dict(cars_per_sector),
            "proximity_metrics": proximity_metrics,
            "total_drivers": total_drivers,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def predict_pit_rejoin_ghost(
        self,
        driver_id: str,
        current_position: int,
        pit_lap: int,
        drivers: List[Dict],
        traffic_density: float,
        total_cars: int,
        sector_at_pit: str = "S2"
    ) -> Dict:
        """
        Predict pit rejoin ghost driver position.
        
        Ghost driver = where driver would be if they didn't pit.
        
        Returns:
        - Ghost position
        - Rejoin position
        - Position difference
        - Time advantage/disadvantage
        """
        # Simulate pit rejoin
        rejoin_result = self.pit_rejoin_sim.simulate_pit_rejoin(
            driver_id=driver_id,
            current_position=current_position,
            pit_lap=pit_lap,
            pit_time=22.0,
            average_lap_time=95.0,
            traffic_density=traffic_density,
            total_cars=total_cars,
            sector_at_pit=sector_at_pit
        )
        
        ghost_position = rejoin_result["ghost_position"]
        rejoin_position = rejoin_result["rejoin_position"]
        
        # Calculate advantage
        position_advantage = ghost_position - rejoin_position  # Positive = ghost is worse (pit was good)
        time_advantage = rejoin_result["time_lost"]  # Time lost due to pit
        
        # Project ghost and rejoin positions on track
        ghost_coords = self._position_to_coordinates(ghost_position, total_cars, "S2")
        rejoin_coords = self._position_to_coordinates(rejoin_position, total_cars, sector_at_pit)
        
        return {
            "driver_id": driver_id,
            "pit_lap": pit_lap,
            "ghost": {
                "position": ghost_position,
                "coordinates": ghost_coords,
                "description": "Position without pit stop"
            },
            "rejoin": {
                "position": rejoin_position,
                "coordinates": rejoin_coords,
                "time_lost": rejoin_result["time_lost"],
                "positions_lost": rejoin_result["positions_lost"]
            },
            "comparison": {
                "position_advantage": position_advantage,
                "time_advantage": time_advantage,
                "pit_worthwhile": position_advantage > 0,  # Ghost worse = pit good
                "net_gain": position_advantage - (time_advantage / 1.0)  # Convert time to positions
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def generate_heatmap(
        self,
        drivers: List[Dict],
        resolution: int = 100
    ) -> Dict:
        """
        Generate traffic density heatmap data.
        
        Returns:
        - Heatmap data points (position, density)
        - Color mapping
        - Sector boundaries
        """
        if not drivers:
            return {
                "heatmap": [],
                "sectors": [],
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        # Create bins for heatmap
        bins = np.linspace(0, 1, resolution)
        heatmap_data = np.zeros(resolution)
        
        # Project drivers to track
        projected = self.project_driver_positions(drivers, 1)
        
        # Count drivers in each bin
        for driver in projected["drivers"]:
            global_pos = driver["coordinates"]["global"]
            bin_index = int(global_pos * resolution)
            bin_index = min(bin_index, resolution - 1)
            heatmap_data[bin_index] += 1
        
        # Normalize to density (0-1)
        max_density = max(heatmap_data) if len(heatmap_data) > 0 else 1
        if max_density > 0:
            heatmap_data = heatmap_data / max_density
        
        # Convert to list of points
        heatmap_points = []
        for i, density in enumerate(heatmap_data):
            position = i / resolution
            heatmap_points.append({
                "position": float(position),
                "density": float(density),
                "color": self._density_to_color(density)
            })
        
        # Sector boundaries
        sectors = []
        for sector, info in self.track_coordinates.items():
            sectors.append({
                "sector": sector,
                "start": info["start"],
                "end": info["end"],
                "type": info["type"]
            })
        
        return {
            "heatmap": heatmap_points,
            "sectors": sectors,
            "resolution": resolution,
            "max_density": float(max_density),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _position_to_coordinates(self, position: int, total_cars: int, sector: str) -> Dict:
        """Convert position to track coordinates."""
        sector_info = self.track_coordinates.get(sector, self.track_coordinates["S1"])
        sector_start = sector_info["start"]
        sector_end = sector_info["end"]
        
        # Position ratio (0-1)
        position_ratio = 1.0 - ((position - 1) / max(total_cars, 1))
        
        # Global position
        global_pos = sector_start + (sector_end - sector_start) * position_ratio
        
        return {
            "global": float(global_pos),
            "sector_local": float(position_ratio),
            "sector": sector
        }
    
    def _density_to_color(self, density: float) -> str:
        """Convert density (0-1) to color hex."""
        if density > 0.7:
            return "#f44336"  # Red - Heavy
        elif density > 0.4:
            return "#ff9800"  # Orange - Moderate
        else:
            return "#4CAF50"  # Green - Clear

