"""
Traffic Density Modeling

Implements traffic density calculation for race analysis.
Used in endurance racing to model time lost in traffic.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional


class TrafficDensityModel:
    """
    Traffic density calculator for race analysis.
    
    Models traffic density per sector and estimates time lost.
    """
    
    def __init__(self, sector_count: int = 3):
        """Initialize traffic density model."""
        self.sector_count = sector_count
    
    def calculate_traffic_density(self, drivers: List[Dict], sector: str = 'S1') -> float:
        """
        Calculate traffic density in a sector.
        
        Args:
            drivers: List of driver data with positions and sectors
            sector: Sector to analyze
        
        Returns:
            Traffic density (0-1 scale)
        """
        # Count drivers in the same sector
        drivers_in_sector = [d for d in drivers if d.get('sector') == sector]
        
        # Density is based on number of cars and proximity
        density = len(drivers_in_sector) / max(len(drivers), 1)
        
        # Adjust based on position spread (closer positions = higher density)
        if len(drivers_in_sector) > 1:
            positions = [d.get('position', 0) for d in drivers_in_sector]
            position_spread = max(positions) - min(positions)
            proximity_factor = 1.0 / (1 + position_spread / 5)  # Closer = higher density
            density *= (1 + proximity_factor)
        
        # Normalize to 0-1
        density = min(1.0, density)
        
        return density
    
    def estimate_time_lost(self, traffic_density: float, sector: str = 'S1') -> float:
        """
        Estimate time lost due to traffic density.
        
        Args:
            traffic_density: Traffic density (0-1)
            sector: Sector being affected
        
        Returns:
            Time lost in seconds
        """
        # Base time loss per sector (seconds)
        base_loss_per_sector = {'S1': 0.3, 'S2': 0.5, 'S3': 0.4}.get(sector, 0.4)
        
        # Scale by density (quadratic relationship)
        time_lost = base_loss_per_sector * (traffic_density ** 1.5)
        
        return time_lost
    
    def analyze_traffic_pattern(self, lap_data: pd.DataFrame) -> Dict:
        """
        Analyze traffic patterns across a race.
        
        Args:
            lap_data: DataFrame with lap data
        
        Returns:
            Dict with traffic analysis
        """
        if 'sector' not in lap_data.columns:
            return {'error': 'Sector data not found'}
        
        # Group by sector
        sector_traffic = {}
        
        for sector in ['S1', 'S2', 'S3']:
            sector_data = lap_data[lap_data.get('sector', '') == sector]
            density = len(sector_data) / max(len(lap_data), 1)
            
            sector_traffic[sector] = {
                'density': density,
                'drivers_count': len(sector_data),
                'avg_time_lost': self.estimate_time_lost(density, sector)
            }
        
        return {
            'sector_traffic': sector_traffic,
            'overall_density': np.mean([s['density'] for s in sector_traffic.values()])
        }


def calculate_traffic_density(drivers: List[Dict], sector: str = 'S1') -> float:
    """Convenience function to calculate traffic density."""
    model = TrafficDensityModel()
    return model.calculate_traffic_density(drivers, sector)

