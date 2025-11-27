"""
Pit Rejoin Simulator

Predicts rejoin position after pit stop and calculates time lost in traffic.
"""

import numpy as np
from typing import Dict, List, Optional
from datetime import datetime


class PitRejoinSimulator:
    """
    Simulates pit stop rejoin scenarios.
    
    Predicts:
    - Rejoin position after pit stop
    - Time lost in traffic during rejoin
    - Ghost driver position (where would we be without pit?)
    - Traffic density impact
    """
    
    def __init__(self):
        self.base_pit_time = 22.0  # Base pit stop time (seconds)
        self.pit_lane_time = 3.0   # Time to travel through pit lane
        self.rejoin_speed_delta = 0.8  # Speed difference when rejoining (0.8x track speed)
        
    def simulate_pit_rejoin(
        self,
        driver_id: str,
        current_position: int,
        pit_lap: int,
        pit_time: float,
        average_lap_time: float,
        traffic_density: float,
        total_cars: int,
        sector_at_pit: str = "S2"
    ) -> Dict:
        """
        Simulate pit stop and predict rejoin position.
        
        Args:
            driver_id: Driver identifier
            current_position: Position before pit stop
            pit_lap: Lap number when pitting
            pit_time: Total pit stop time (seconds)
            average_lap_time: Average lap time for field (seconds)
            traffic_density: Traffic density (0.0 to 1.0)
            total_cars: Total number of cars in race
            sector_at_pit: Sector where pit entry occurs
            
        Returns:
            Complete rejoin simulation results
        """
        # Calculate how many cars pass during pit stop
        # Time lost = pit_time + rejoin time
        total_time_lost = pit_time + self._calculate_rejoin_time_loss(
            traffic_density=traffic_density,
            sector=sector_at_pit,
            average_lap_time=average_lap_time
        )
        
        # Convert time lost to positions lost
        # Each position is roughly 0.5-2 seconds depending on field spread
        positions_lost = self._time_to_positions(total_time_lost, average_lap_time)
        
        # Predict rejoin position
        rejoin_position = min(current_position + positions_lost, total_cars)
        
        # Calculate ghost position (where would we be without pit?)
        ghost_position = self._calculate_ghost_position(
            current_position=current_position,
            pit_lap=pit_lap,
            average_lap_time=average_lap_time
        )
        
        # Traffic impact during rejoin
        traffic_impact = self._calculate_traffic_impact(
            rejoin_position=rejoin_position,
            traffic_density=traffic_density,
            sector=sector_at_pit
        )
        
        return {
            "driver_id": driver_id,
            "pit_lap": pit_lap,
            "position_before_pit": current_position,
            "rejoin_position": int(rejoin_position),
            "positions_lost": int(positions_lost),
            "time_lost": float(total_time_lost),
            "ghost_position": int(ghost_position),
            "traffic_impact": traffic_impact,
            "rejoin_sector": sector_at_pit,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _calculate_rejoin_time_loss(
        self,
        traffic_density: float,
        sector: str,
        average_lap_time: float
    ) -> float:
        """
        Calculate additional time lost during rejoin due to traffic.
        
        Rejoining driver must:
        - Merge safely into traffic
        - May be stuck behind slower cars
        - Lose momentum in traffic
        """
        # Base rejoin penalty (merging, speed loss)
        base_rejoin_penalty = 1.5  # seconds
        
        # Traffic density multiplier
        # Higher density = more time lost
        traffic_multiplier = 1.0 + (traffic_density * 0.5)
        
        # Sector-specific penalties
        sector_penalties = {
            "S1": 0.8,   # Straight sections - easier to rejoin
            "S2": 1.2,   # Technical sections - harder to rejoin
            "S3": 1.0    # Mixed sections
        }
        sector_mult = sector_penalties.get(sector, 1.0)
        
        # Total rejoin time loss
        rejoin_loss = base_rejoin_penalty * traffic_multiplier * sector_mult
        
        return rejoin_loss
    
    def _time_to_positions(self, time_lost: float, average_lap_time: float) -> float:
        """
        Convert time lost to positions lost.
        
        Assumes field spread of ~0.5-2 seconds per position.
        """
        # Average gap between positions (seconds)
        # In close racing: ~0.5s, in spread out field: ~2s
        avg_gap_per_position = 1.0  # Conservative estimate
        
        positions_lost = time_lost / avg_gap_per_position
        
        return max(0.0, positions_lost)
    
    def _calculate_ghost_position(
        self,
        current_position: int,
        pit_lap: int,
        average_lap_time: float
    ) -> int:
        """
        Calculate where driver would be if they didn't pit (ghost driver).
        
        This helps evaluate if pit stop was worth it.
        """
        # Ghost driver continues with degrading tires
        # Assume 0.1s per lap degradation after pit window
        degradation_per_lap = 0.1
        
        # Estimate how many laps since pit window opened
        laps_since_pit_window = max(0, pit_lap - 15)  # Pit window typically opens around lap 15
        
        # Ghost driver loses time due to degradation
        ghost_time_loss = laps_since_pit_window * degradation_per_lap
        
        # Convert to positions (ghost would lose positions due to slower pace)
        ghost_positions_lost = ghost_time_loss / 1.0  # 1 second per position
        
        # Ghost position (worse than current if degradation is significant)
        ghost_position = min(current_position + int(ghost_positions_lost), current_position + 5)
        
        return ghost_position
    
    def _calculate_traffic_impact(
        self,
        rejoin_position: int,
        traffic_density: float,
        sector: str
    ) -> Dict:
        """
        Calculate traffic impact after rejoin.
        
        Returns time lost per lap due to traffic.
        """
        # Cars ahead after rejoin
        cars_ahead = max(0, rejoin_position - 1)
        
        # Base traffic penalty per car
        base_penalty = 0.1  # seconds per car per lap
        
        # Sector multipliers
        sector_multipliers = {
            "S1": 0.8,   # Less impact in straights
            "S2": 1.3,   # More impact in technical sections
            "S3": 1.0
        }
        sector_mult = sector_multipliers.get(sector, 1.0)
        
        # Traffic density multiplier
        density_mult = 1.0 + (traffic_density * 0.5)
        
        # Total traffic impact per lap
        traffic_loss_per_lap = cars_ahead * base_penalty * sector_mult * density_mult
        
        return {
            "cars_ahead": cars_ahead,
            "traffic_loss_per_lap": float(traffic_loss_per_lap),
            "sector": sector,
            "density": float(traffic_density),
            "clear_window": traffic_loss_per_lap < 0.2
        }
    
    def predict_optimal_pit_window(
        self,
        current_position: int,
        traffic_density: float,
        tire_age: int,
        degradation_rate: float,
        total_laps: int,
        current_lap: int
    ) -> Dict:
        """
        Predict optimal pit window considering traffic.
        
        Returns best lap range to pit for minimal traffic impact.
        """
        # Ideal pit window (when traffic is lowest)
        # Typically around lap 15-25 for most races
        
        # Calculate traffic density over next 10 laps
        traffic_forecast = []
        for lap in range(current_lap, min(current_lap + 10, total_laps)):
            # Traffic typically decreases as field spreads out
            predicted_density = traffic_density * (1.0 - (lap - current_lap) * 0.05)
            traffic_forecast.append({
                "lap": lap,
                "traffic_density": max(0.0, predicted_density),
                "suitable": predicted_density < 0.4  # Low traffic = suitable
            })
        
        # Find best window (lowest traffic)
        best_window = min(traffic_forecast, key=lambda x: x["traffic_density"])
        
        # Consider degradation urgency
        degradation_urgent = tire_age > 20 or degradation_rate > 0.003
        
        return {
            "optimal_lap": best_window["lap"],
            "optimal_window": {
                "start": max(current_lap, best_window["lap"] - 2),
                "end": min(total_laps, best_window["lap"] + 2)
            },
            "traffic_forecast": traffic_forecast,
            "degradation_urgent": degradation_urgent,
            "recommendation": "PIT_NOW" if degradation_urgent else "PIT_IN_WINDOW"
        }


def simulate_pit_rejoin(
    driver_id: str,
    current_position: int,
    pit_lap: int,
    **kwargs
) -> Dict:
    """
    Convenience function to simulate pit rejoin.
    """
    simulator = PitRejoinSimulator()
    return simulator.simulate_pit_rejoin(
        driver_id=driver_id,
        current_position=current_position,
        pit_lap=pit_lap,
        **kwargs
    )


if __name__ == "__main__":
    # Test pit rejoin simulator
    simulator = PitRejoinSimulator()
    
    result = simulator.simulate_pit_rejoin(
        driver_id="driver_1",
        current_position=5,
        pit_lap=20,
        pit_time=22.0,
        average_lap_time=95.0,
        traffic_density=0.6,
        total_cars=20,
        sector_at_pit="S2"
    )
    
    print("Pit Rejoin Simulation:")
    print(result)
    
    # Test optimal pit window
    window = simulator.predict_optimal_pit_window(
        current_position=5,
        traffic_density=0.6,
        tire_age=18,
        degradation_rate=0.0025,
        total_laps=50,
        current_lap=15
    )
    
    print("\nOptimal Pit Window:")
    print(window)

