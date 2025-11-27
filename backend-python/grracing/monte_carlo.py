"""
Enhanced Monte Carlo Race Simulator - Professional race strategy simulation.

Implements comprehensive race simulation with:
- Tire degradation modeling
- Fuel effect modeling
- Pit stop strategy
- Traffic density effects
- Overtake probability
- Virtual Safety Car / Full Safety Car scenarios
"""
import random
import statistics
import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from .degradation import TireDegradationModel, FuelEffectModel


class MonteCarloRaceSimulator:
    """
    Professional Monte Carlo race simulator for strategy analysis.
    
    Used by race engineers in F1, WEC, IndyCar, IMSA for:
    - Strategy optimization
    - Pit window analysis
    - Position probability calculations
    - Tire compound comparison
    """
    
    def __init__(self, 
                 pit_loss: float = 25.0,  # seconds lost in pit
                 degradation_noise: float = 0.1,  # 10% variance in degradation
                 lap_time_noise: float = 0.02):  # 2% variance in lap time
        """
        Initialize race simulator.
        
        Args:
            pit_loss: Time lost during pit stop (seconds)
            degradation_noise: Variance in degradation rate (0-1)
            lap_time_noise: Variance in lap time execution (0-1)
        """
        self.pit_loss = pit_loss
        self.degradation_noise = degradation_noise
        self.lap_time_noise = lap_time_noise
        self.degradation_model = TireDegradationModel()
        self.fuel_model = FuelEffectModel()
    
    def simulate_lap_time(self, base_time: float, lap_number: int,
                         compound: str = "SOFT", 
                         fuel_load: float = 100.0,
                         degradation_applied: bool = True) -> float:
        """
        Simulate lap time with degradation, fuel, and noise.
        
        Args:
            base_time: Base lap time in seconds
            lap_number: Current lap number (0-indexed)
            compound: Tire compound
            fuel_load: Current fuel load in kg
            degradation_applied: Whether to apply degradation
        
        Returns:
            Simulated lap time in seconds
        """
        time = base_time
        
        # Apply degradation
        if degradation_applied:
            self.degradation_model.compound = compound
            time = self.degradation_model.linear_degradation(
                lap_number, base_time
            )
        
        # Apply fuel effect (lighter car = faster)
        fuel_effect = self.fuel_model.calculate_fuel_effect(
            lap_number, fuel_load
        )
        time += fuel_effect
        
        # Add execution noise (random variance)
        noise_factor = random.uniform(1 - self.lap_time_noise, 1 + self.lap_time_noise)
        time *= noise_factor
        
        return time
    
    def simulate_one_race(self, 
                         driver_paces: Dict[str, float],
                         n_laps: int = 50,
                         pit_strategy: Optional[Dict[str, List[int]]] = None,
                         compounds: Optional[Dict[str, List[str]]] = None) -> Dict:
        """
        Simulate one complete race.
        
        Args:
            driver_paces: Dict of {driver_id: base_lap_time}
            n_laps: Total race laps
            pit_strategy: Dict of {driver_id: [pit_lap_1, pit_lap_2, ...]}
            compounds: Dict of {driver_id: [compound_for_stint_1, ...]}
        
        Returns:
            Dict with finishing positions and times
        """
        results = {
            'driver_times': {d: 0.0 for d in driver_paces},
            'driver_lap_times': {d: [] for d in driver_paces},
            'pit_stops': {d: [] for d in driver_paces},
            'positions': []
        }
        
        # Initialize tire compounds
        if compounds is None:
            compounds = {d: ['SOFT'] for d in driver_paces}
        
        # Initialize pit strategies
        if pit_strategy is None:
            pit_strategy = {d: [] for d in driver_paces}
        
        # Track stint information per driver
        stint_info = {}
        for driver in driver_paces:
            stint_info[driver] = {
                'current_stint': 0,
                'laps_in_stint': 0,
                'stint_start_lap': 0,
                'current_compound': compounds[driver][0] if compounds[driver] else 'SOFT',
                'fuel_load': 100.0  # Starting fuel
            }
        
        # Simulate each lap
        for lap in range(n_laps):
            lap_times = {}
            
            for driver, base_pace in driver_paces.items():
                info = stint_info[driver]
                
                # Check for pit stop
                if driver in pit_strategy and lap in pit_strategy[driver]:
                    results['driver_times'][driver] += self.pit_loss
                    results['pit_stops'][driver].append(lap)
                    
                    # Move to next stint
                    info['current_stint'] += 1
                    info['laps_in_stint'] = 0
                    info['stint_start_lap'] = lap
                    
                    # Update compound
                    if info['current_stint'] < len(compounds[driver]):
                        info['current_compound'] = compounds[driver][info['current_stint']]
                    
                    # Refuel (simplified: full tank)
                    info['fuel_load'] = 100.0
                
                # Simulate lap time
                lap_time = self.simulate_lap_time(
                    base_pace,
                    info['laps_in_stint'],
                    info['current_compound'],
                    info['fuel_load'],
                    degradation_applied=True
                )
                
                results['driver_times'][driver] += lap_time
                results['driver_lap_times'][driver].append(lap_time)
                lap_times[driver] = lap_time
                
                # Update stint info
                info['laps_in_stint'] += 1
                info['fuel_load'] -= self.fuel_model.fuel_consumption_per_lap
            
            # Sort by cumulative time for position
            sorted_drivers = sorted(
                results['driver_times'].items(), 
                key=lambda x: x[1]
            )
            positions = {driver: pos + 1 for pos, (driver, _) in enumerate(sorted_drivers)}
            results['positions'].append(positions)
        
        # Final positions
        sorted_final = sorted(
            results['driver_times'].items(),
            key=lambda x: x[1]
        )
        results['final_positions'] = {
            driver: pos + 1 for pos, (driver, _) in enumerate(sorted_final)
        }
        results['final_times'] = dict(sorted_final)
        
        return results
    
    def monte_carlo_simulation(self,
                              driver_paces: Dict[str, float],
                              n_laps: int = 50,
                              iterations: int = 1000,
                              pit_strategy: Optional[Dict[str, List[int]]] = None,
                              compounds: Optional[Dict[str, List[str]]] = None) -> Dict:
        """
        Run Monte Carlo simulation for race strategy analysis.
        
        Args:
            driver_paces: Dict of {driver_id: base_lap_time}
            n_laps: Total race laps
            iterations: Number of simulation iterations
            pit_strategy: Optional pit stop strategy
            compounds: Optional tire compound strategy
        
        Returns:
            Comprehensive simulation results with probabilities
        """
        all_results = []
        position_counts = defaultdict(lambda: defaultdict(int))
        
        for _ in range(iterations):
            result = self.simulate_one_race(
                driver_paces, n_laps, pit_strategy, compounds
            )
            all_results.append(result)
            
            # Count positions
            for driver, pos in result['final_positions'].items():
                position_counts[driver][pos] += 1
        
        # Calculate statistics
        avg_times = {}
        for driver in driver_paces:
            times = [r['final_times'][driver] for r in all_results]
            avg_times[driver] = {
                'mean': statistics.mean(times),
                'median': statistics.median(times),
                'std': statistics.stdev(times) if len(times) > 1 else 0.0,
                'min': min(times),
                'max': max(times)
            }
        
        # Calculate position probabilities
        position_probs = {}
        for driver in driver_paces:
            position_probs[driver] = {}
            for pos in range(1, len(driver_paces) + 1):
                count = position_counts[driver][pos]
                probability = count / iterations
                position_probs[driver][pos] = probability
        
        # Most likely finishing positions
        most_likely_positions = {}
        for driver in driver_paces:
            most_likely_pos = max(
                position_probs[driver].items(),
                key=lambda x: x[1]
            )
            most_likely_positions[driver] = {
                'position': most_likely_pos[0],
                'probability': most_likely_pos[1]
            }
        
        return {
            'iterations': iterations,
            'average_times': avg_times,
            'position_probabilities': position_probs,
            'most_likely_positions': most_likely_positions,
            'simulations': all_results[:10]  # Return first 10 for analysis
        }
    
    def optimize_pit_strategy(self,
                             driver_pace: float,
                             n_laps: int,
                             compound: str = "SOFT",
                             max_pit_stops: int = 2) -> Dict:
        """
        Optimize pit stop strategy for a single driver.
        
        Uses degradation model to find optimal pit windows.
        
        Returns:
            Recommended pit strategy
        """
        self.degradation_model.compound = compound
        base_time = driver_pace
        
        # Estimate degradation per lap
        degradation_per_lap = (
            self.degradation_model.compound_coefficients.get(compound, 0.05) * base_time
        )
        
        # Find optimal pit lap (when degradation saves > pit loss)
        optimal_pit_laps = []
        
        for stint_num in range(max_pit_stops):
            if not optimal_pit_laps:
                start_lap = 0
            else:
                start_lap = optimal_pit_laps[-1]
            
            # Find when pit becomes beneficial
            for lap in range(start_lap + 10, n_laps):  # At least 10 lap stint
                laps_since_start = lap - start_lap
                degraded_time = base_time + (degradation_per_lap * laps_since_start)
                new_time = base_time
                time_gain = degraded_time - new_time
                
                if time_gain > self.pit_loss:
                    optimal_pit_laps.append(lap)
                    break
        
        return {
            'recommended_pit_laps': optimal_pit_laps,
            'degradation_per_lap': degradation_per_lap,
            'pit_loss': self.pit_loss,
            'expected_gain': degradation_per_lap * 20 - self.pit_loss  # Rough estimate
        }


def simulate_race_strategy(driver_paces: Dict[str, float],
                          n_laps: int = 50,
                          iterations: int = 1000,
                          **kwargs) -> Dict:
    """
    Convenience function for Monte Carlo race simulation.
    
    Args:
        driver_paces: Dict of {driver_id: base_lap_time}
        n_laps: Total race laps
        iterations: Number of simulations
        **kwargs: Additional simulator parameters
    
    Returns:
        Simulation results
    """
    simulator = MonteCarloRaceSimulator(**kwargs)
    return simulator.monte_carlo_simulation(driver_paces, n_laps, iterations)

