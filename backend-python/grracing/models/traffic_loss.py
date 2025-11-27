"""
Traffic Loss Model

Calculates time lost due to traffic (cars ahead, sector density, etc.)
"""

import numpy as np
from typing import Dict, List, Optional


class TrafficLossModel:
    """
    Traffic loss prediction model.
    
    Calculates:
    - Clean air delta
    - Traffic penalty per car ahead
    - Sector-based traffic cost
    """
    
    def __init__(self):
        self.base_penalty_per_car = 0.1  # Base time loss per car ahead (seconds)
        self.sector_multipliers = {
            "S1": 1.0,  # Straight sections - less impact
            "S2": 1.2,  # Technical sections - more impact
            "S3": 1.1   # Mixed sections - moderate impact
        }
    
    def calculate_traffic_loss(
        self,
        cars_ahead: int,
        sector: str = "S2",
        traffic_density: float = 0.5,
        driver_position: int = 5,
        total_cars: int = 20
    ) -> Dict:
        """
        Calculate time lost due to traffic.
        
        Args:
            cars_ahead: Number of cars directly ahead
            sector: Current sector (S1, S2, S3)
            traffic_density: Traffic density in sector (0.0 to 1.0)
            driver_position: Current position in race
            total_cars: Total number of cars in race
            
        Returns:
            Traffic loss breakdown
        """
        # Clean air benefit (leader has no traffic)
        clean_air_delta = 0.0 if cars_ahead == 0 else -0.2  # Leader gains ~0.2s
        
        # Base traffic penalty per car
        base_penalty = cars_ahead * self.base_penalty_per_car
        
        # Sector-specific multiplier
        sector_mult = self.sector_multipliers.get(sector, 1.0)
        sector_penalty = base_penalty * sector_mult
        
        # Traffic density penalty (overall traffic in sector)
        density_penalty = traffic_density * 0.3  # Up to 0.3s additional loss
        
        # Position-based penalty (more cars = more chaos)
        position_factor = driver_position / total_cars  # 0 to 1
        position_penalty = position_factor * 0.2  # Up to 0.2s
        
        # Total traffic loss
        total_loss = sector_penalty + density_penalty + position_penalty
        
        # Random variation (±10%)
        variation = np.random.uniform(-0.1, 0.1) * total_loss
        total_loss += variation
        
        # Ensure non-negative
        total_loss = max(0.0, total_loss)
        
        return {
            "cars_ahead": cars_ahead,
            "clean_air_delta": float(clean_air_delta),
            "base_penalty": float(base_penalty),
            "sector_penalty": float(sector_penalty),
            "density_penalty": float(density_penalty),
            "position_penalty": float(position_penalty),
            "total_traffic_loss": float(total_loss),
            "sector": sector,
            "traffic_density": float(traffic_density)
        }
    
    def predict_stint_traffic_loss(
        self,
        laps: int,
        average_cars_ahead: float,
        sector_distribution: Dict[str, float],
        traffic_trend: str = "stable"
    ) -> Dict:
        """
        Predict cumulative traffic loss over a stint.
        
        Args:
            laps: Number of laps in stint
            average_cars_ahead: Average number of cars ahead
            sector_distribution: Distribution of time in each sector (S1, S2, S3)
            traffic_trend: "improving", "stable", "degrading"
            
        Returns:
            Cumulative traffic loss prediction
        """
        # Base loss per lap
        base_loss = average_cars_ahead * self.base_penalty_per_car
        
        # Sector-weighted average multiplier
        sector_avg_mult = sum(
            sector_distribution.get(sector, 0.33) * self.sector_multipliers.get(sector, 1.0)
            for sector in ["S1", "S2", "S3"]
        )
        
        # Loss per lap
        loss_per_lap = base_loss * sector_avg_mult
        
        # Adjust for traffic trend
        trend_multipliers = {
            "improving": 0.8,  # Traffic clearing
            "stable": 1.0,
            "degrading": 1.2   # More traffic ahead
        }
        loss_per_lap *= trend_multipliers.get(traffic_trend, 1.0)
        
        # Cumulative loss
        total_loss = loss_per_lap * laps
        
        return {
            "stint_laps": laps,
            "loss_per_lap": float(loss_per_lap),
            "total_traffic_loss": float(total_loss),
            "average_cars_ahead": float(average_cars_ahead),
            "traffic_trend": traffic_trend
        }
    
    def calculate_clean_air_delta(self, position: int) -> float:
        """
        Calculate time advantage of clean air (being in front).
        
        Leader typically has 0.1-0.3s advantage per lap.
        """
        if position == 1:
            return 0.2  # Leader gets clean air bonus
        elif position <= 3:
            return 0.1  # Podium positions get some benefit
        else:
            return 0.0  # No clean air benefit


if __name__ == "__main__":
    # Test traffic loss model
    model = TrafficLossModel()
    
    # Calculate traffic loss
    loss = model.calculate_traffic_loss(
        cars_ahead=3,
        sector="S2",
        traffic_density=0.7,
        driver_position=5,
        total_cars=20
    )
    
    print("Traffic loss breakdown:", loss)
    
    # Predict stint loss
    stint_loss = model.predict_stint_traffic_loss(
        laps=20,
        average_cars_ahead=2.5,
        sector_distribution={"S1": 0.33, "S2": 0.34, "S3": 0.33},
        traffic_trend="stable"
    )
    
    print("Stint traffic loss:", stint_loss)

