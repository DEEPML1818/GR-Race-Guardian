"""
Overtake Probability Model

Implements overtake probability calculation based on:
- Speed differential
- Position
- Tire age
- Sector characteristics
"""
import numpy as np
import pandas as pd
from typing import Dict, Optional
from sklearn.ensemble import RandomForestClassifier


class OvertakeProbabilityModel:
    """
    Overtake probability calculator for race analysis.
    
    Used to predict likelihood of overtaking based on driver and race conditions.
    """
    
    def __init__(self):
        """Initialize overtake probability model."""
        self.model = None
        self.trained = False
    
    def calculate_overtake_probability(self,
                                      attacker_speed: float,
                                      defender_speed: float,
                                      attacker_position: int,
                                      defender_position: int,
                                      attacker_tire_age: int,
                                      defender_tire_age: int,
                                      sector: str = 'S2') -> float:
        """
        Calculate overtake probability based on driver conditions.
        
        Args:
            attacker_speed: Speed of attacking driver (km/h)
            defender_speed: Speed of defending driver (km/h)
            attacker_position: Position of attacking driver
            defender_position: Position of defending driver
            attacker_tire_age: Tire age of attacking driver (laps)
            defender_tire_age: Tire age of defending driver (laps)
            sector: Current sector (S1, S2, S3)
        
        Returns:
            Probability of overtake (0-1)
        """
        # Speed differential (higher = better chance)
        speed_delta = attacker_speed - defender_speed
        speed_advantage = (speed_delta / defender_speed) * 0.5 if defender_speed > 0 else 0
        
        # Position proximity (closer = better chance)
        position_proximity = 1.0 / abs(attacker_position - defender_position) if attacker_position != defender_position else 0
        
        # Tire age advantage (fresher tires = better chance)
        tire_age_delta = defender_tire_age - attacker_tire_age
        tire_advantage = min(tire_age_delta / 20, 0.5)  # Max 0.5 bonus for 20+ lap fresher tires
        
        # Sector characteristics (some sectors easier to overtake)
        sector_factor = {'S1': 0.3, 'S2': 0.5, 'S3': 0.4}.get(sector, 0.4)
        
        # Base probability
        base_prob = 0.1
        
        # Calculate final probability
        probability = (
            base_prob +
            speed_advantage * 0.4 +
            position_proximity * 0.2 +
            tire_advantage * 0.2 +
            sector_factor * 0.1
        )
        
        # Normalize to 0-1 range
        probability = max(0.0, min(1.0, probability))
        
        return probability
    
    def predict_overtake(self, driver_data: Dict) -> Dict:
        """
        Predict overtake probability for multiple driver pairs.
        
        Args:
            driver_data: Dict with driver information
        
        Returns:
            Dict with overtake probabilities
        """
        results = {}
        
        # Example: compare each driver with others
        drivers = driver_data.get('drivers', [])
        
        for i, attacker in enumerate(drivers):
            for j, defender in enumerate(drivers):
                if i != j and attacker['position'] > defender['position']:
                    prob = self.calculate_overtake_probability(
                        attacker.get('speed', 150),
                        defender.get('speed', 150),
                        attacker.get('position', 10),
                        defender.get('position', 10),
                        attacker.get('tire_age', 10),
                        defender.get('tire_age', 10),
                        attacker.get('sector', 'S2')
                    )
                    
                    key = f"{attacker.get('id')}_vs_{defender.get('id')}"
                    results[key] = {
                        'probability': prob,
                        'attacker': attacker.get('id'),
                        'defender': defender.get('id'),
                        'likely': prob > 0.5
                    }
        
        return results


def calculate_overtake_probability(attacker_speed: float, defender_speed: float,
                                  attacker_position: int, defender_position: int,
                                  attacker_tire_age: int = 10,
                                  defender_tire_age: int = 10,
                                  sector: str = 'S2') -> float:
    """Convenience function to calculate overtake probability."""
    model = OvertakeProbabilityModel()
    return model.calculate_overtake_probability(
        attacker_speed, defender_speed,
        attacker_position, defender_position,
        attacker_tire_age, defender_tire_age,
        sector
    )

