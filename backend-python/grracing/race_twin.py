"""
Digital Race Twin - Complete Monte Carlo Race Simulation Engine

Simulates future race outcomes using Monte Carlo methods.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
from collections import Counter

from .driver_twin import DriverTwinGenerator
from .degradation import TireDegradationModel
from .overtake import OvertakeProbabilityModel
from .traffic import TrafficDensityModel
from .weather import WeatherModel
from .pit_rejoin import PitRejoinSimulator
from .strategy_optimizer import StrategyOptimizer


class RaceTwinSimulator:
    """
    Monte Carlo race simulation engine.
    
    Simulates 100-500 race outcomes to predict finishing positions,
    pit strategies, and race probabilities.
    """
    
    def __init__(self, num_simulations: int = 500):
        self.num_simulations = max(100, min(num_simulations, 500))  # Clamp to 100-500
        self.driver_twin_gen = DriverTwinGenerator()
        self.degradation_model = TireDegradationModel()
        self.overtake_model = OvertakeProbabilityModel()
        self.traffic_model = TrafficDensityModel()
        self.weather_model = WeatherModel()
        self.pit_rejoin_sim = PitRejoinSimulator()
        self.strategy_optimizer = StrategyOptimizer()
        
    def simulate_race(
        self,
        race_id: str,
        drivers: List[Dict],
        total_laps: int,
        current_lap: int = 1,
        weather_data: Optional[Dict] = None,
        pit_strategy_options: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Run Monte Carlo race simulation.
        
        Args:
            race_id: Race identifier
            drivers: List of driver data with current positions, lap times, etc.
            total_laps: Total race distance
            current_lap: Current lap number
            weather_data: Optional weather conditions
            pit_strategy_options: Optional pit strategy constraints
            
        Returns:
            Complete Race Twin JSON with probabilities and recommendations
        """
        # Generate Driver Twins for all drivers
        driver_twins = {}
        for driver in drivers:
            twin = self._generate_twin_from_driver(driver)
            driver_twins[driver['id']] = twin
        
        # Run Monte Carlo simulations
        simulation_results = []
        for sim_num in range(self.num_simulations):
            result = self._simulate_single_race(
                drivers=drivers,
                driver_twins=driver_twins,
                total_laps=total_laps,
                current_lap=current_lap,
                weather_data=weather_data,
                pit_strategy_options=pit_strategy_options
            )
            simulation_results.append(result)
        
        # Analyze results
        finishing_positions = self._analyze_finishing_positions(simulation_results)
        pit_recommendations = self._analyze_pit_strategies(simulation_results, drivers, driver_twins, current_lap, total_laps)
        tire_cliff = self._predict_tire_cliff(driver_twins, current_lap)
        traffic_simulation = self._simulate_traffic_scenarios(simulation_results, drivers)
        undercut_outcomes = self._analyze_undercut_outcomes(simulation_results, drivers, driver_twins)
        
        # Build complete RaceTwin JSON
        race_twin = {
            "race_id": race_id,
            "simulations": self.num_simulations,
            "current_lap": current_lap,
            "total_laps": total_laps,
            "expected_finishing_positions": finishing_positions,
            "pit_recommendations": pit_recommendations,
            "tire_cliff_prediction": tire_cliff,
            "traffic_simulation": traffic_simulation,
            "undercut_outcomes": undercut_outcomes,
            "monte_carlo_outcomes": {
                "win_probability": finishing_positions[0].get("probability", 0.0) if finishing_positions else 0.0,
                "podium_probability": sum(p.get("probability", 0.0) for p in finishing_positions[:3] if finishing_positions) if finishing_positions else 0.0,
                "points_probability": sum(p.get("probability", 0.0) for p in finishing_positions[:10] if finishing_positions) if finishing_positions else 0.0
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "confidence": min(current_lap / 10.0, 1.0)  # More laps = higher confidence
        }
        
        return race_twin
    
    def _simulate_single_race(
        self,
        drivers: List[Dict],
        driver_twins: Dict,
        total_laps: int,
        current_lap: int,
        weather_data: Optional[Dict] = None,
        pit_strategy_options: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Simulate a single race outcome.
        
        Returns finishing positions and pit stop information.
        """
        # Initialize race state
        race_state = {
            driver['id']: {
                'driver_id': driver['id'],
                'position': driver.get('position', 0),
                'lap_times': [],
                'pit_stops': [],
                'tire_age': driver.get('tire_age', 0),
                'tire_compound': driver.get('tire_compound', 'MEDIUM'),
                'total_time': 0.0,
                'twin': driver_twins.get(driver['id'])
            }
            for driver in drivers
        }
        
        # Simulate remaining laps
        for lap in range(current_lap, total_laps + 1):
            # Calculate lap times for each driver
            for driver_id, state in race_state.items():
                lap_time = self._calculate_lap_time(
                    driver_id=driver_id,
                    state=state,
                    lap=lap,
                    weather_data=weather_data,
                    drivers=race_state
                )
                state['lap_times'].append(lap_time)
                state['total_time'] += lap_time
                state['tire_age'] += 1
                
                # Apply tire degradation
                degradation = self.degradation_model.calculate_degradation(
                    tire_age=state['tire_age'],
                    compound=state['tire_compound'],
                    track_temp=weather_data.get('track_temp', 25) if weather_data else 25
                )
                
                # Simulate pit stops
                should_pit = self._should_pit(
                    driver_id=driver_id,
                    state=state,
                    lap=lap,
                    total_laps=total_laps,
                    pit_strategy_options=pit_strategy_options
                )
                
                if should_pit:
                    pit_result = self._simulate_pit_stop(state, lap, race_state, len(drivers))
                    state['pit_stops'].append(pit_result)
                    state['total_time'] += pit_result['pit_time']
                    state['tire_age'] = 0
                    state['tire_compound'] = pit_result.get('new_compound', 'MEDIUM')
                    # Update position based on rejoin
                    state['position'] = pit_result.get('rejoin_position', state['position'])
                
                # Simulate overtakes
                self._simulate_overtakes(state, race_state, lap)
            
            # Update positions based on total time
            sorted_drivers = sorted(
                race_state.items(),
                key=lambda x: x[1]['total_time']
            )
            for new_pos, (driver_id, _) in enumerate(sorted_drivers, 1):
                race_state[driver_id]['position'] = new_pos
        
        # Extract finishing positions
        final_positions = sorted(
            [(driver_id, state['total_time']) for driver_id, state in race_state.items()],
            key=lambda x: x[1]
        )
        
        return {
            'finishing_order': [driver_id for driver_id, _ in final_positions],
            'pit_stops': {driver_id: state['pit_stops'] for driver_id, state in race_state.items()},
            'total_times': {driver_id: state['total_time'] for driver_id, state in race_state.items()}
        }
    
    def _calculate_lap_time(
        self,
        driver_id: str,
        state: Dict,
        lap: int,
        weather_data: Optional[Dict],
        drivers: Dict
    ) -> float:
        """
        Calculate lap time for a driver at a specific lap.
        
        Considers: base pace, degradation, traffic, weather, twin metrics.
        """
        twin = state.get('twin', {})
        base_pace = twin.get('pace_vector', 0.0)
        base_lap_time = 95.0  # Default base time
        
        # Adjust for pace vector (negative = faster)
        adjusted_time = base_lap_time * (1.0 + base_pace)
        
        # Apply tire degradation using proper degradation model
        tire_age = state.get('tire_age', 0)
        tire_compound = state.get('tire_compound', 'MEDIUM')
        track_temp = weather_data.get('track_temp', 25) if weather_data else 25
        
        # Create degradation model for this compound
        degradation_model = TireDegradationModel(compound=tire_compound, track_temp=track_temp)
        
        # Get base pace from twin or default
        base_pace = twin.get('degradation_profile', {}).get('base_pace', adjusted_time)
        
        # Calculate degraded lap time using exponential model
        degraded_time = degradation_model.exponential_degradation(
            lap_number=tire_age,
            base_time=base_pace
        )
        
        # Calculate degradation factor
        degradation_factor = (degraded_time - base_pace) / base_pace if base_pace > 0 else tire_age * 0.002
        adjusted_time = degraded_time
        
        # Apply weather effects
        if weather_data:
            weather_modifier = self.weather_model.calculate_pace_modifier(
                track_temp=weather_data.get('track_temp', 25),
                ambient_temp=weather_data.get('ambient_temp', 25),
                humidity=weather_data.get('humidity', 50),
                rainfall=weather_data.get('rainfall', 0)
            )
            adjusted_time *= weather_modifier
        
        # Apply traffic effects
        sector = ['S1', 'S2', 'S3'][(lap - 1) % 3]  # Rotate through sectors
        traffic_penalty = self._calculate_traffic_penalty(
            driver_id=driver_id,
            position=state['position'],
            drivers=drivers,
            sector=sector
        )
        adjusted_time += traffic_penalty
        
        # Add random variance (consistency affects variance)
        consistency = twin.get('consistency_index', 0.8)
        variance = (1.0 - consistency) * 0.5  # Less consistent = more variance
        random_factor = np.random.normal(0, variance)
        adjusted_time += random_factor
        
        return max(adjusted_time, 90.0)  # Minimum lap time cap
    
    def _should_pit(
        self,
        driver_id: str,
        state: Dict,
        lap: int,
        total_laps: int,
        pit_strategy_options: Optional[List[Dict]]
    ) -> bool:
        """
        Determine if driver should pit at this lap.
        """
        # Check strategy constraints
        if pit_strategy_options:
            for strategy in pit_strategy_options:
                if strategy.get('driver_id') == driver_id:
                    planned_pits = strategy.get('planned_pits', [])
                    if lap in planned_pits:
                        return True
        
        # Automatic pit decision based on tire age
        tire_age = state.get('tire_age', 0)
        degradation_profile = state.get('twin', {}).get('degradation_profile', {})
        degradation_rate = degradation_profile.get('rate', 0.002)
        
        # Critical tire age threshold
        critical_age = 20 if degradation_rate < 0.003 else 15
        
        if tire_age >= critical_age:
            # Check if enough laps remaining for fresh tires
            laps_remaining = total_laps - lap
            if laps_remaining >= 10:  # Need at least 10 laps for fresh tires to be worth it
                return True
        
        # Random pit stops (some variability)
        if tire_age > 25 and np.random.random() < 0.1:  # 10% chance to pit if very old tires
            return True
        
        return False
    
    def _simulate_pit_stop(self, state: Dict, lap: int, drivers: Dict, total_cars: int) -> Dict:
        """
        Simulate a pit stop with rejoin traffic simulation.
        
        Returns pit stop time, new tire compound, and rejoin position.
        """
        # Standard pit stop time: 20-25 seconds
        base_pit_time = 22.0
        pit_time_variance = np.random.uniform(-2, 2)
        total_pit_time = base_pit_time + pit_time_variance
        
        # Choose new compound (usually harder compound)
        current_compound = state.get('tire_compound', 'MEDIUM')
        compound_sequence = ['SOFT', 'MEDIUM', 'HARD']
        current_idx = compound_sequence.index(current_compound) if current_compound in compound_sequence else 1
        
        # Usually go to harder compound, sometimes stay same
        if np.random.random() < 0.7:  # 70% chance to go harder
            new_idx = min(current_idx + 1, len(compound_sequence) - 1)
        else:
            new_idx = current_idx
        
        new_compound = compound_sequence[new_idx]
        
        # Simulate pit rejoin using PitRejoinSimulator
        current_position = state.get('position', 1)
        average_lap_time = np.mean([s.get('lap_times', [95.0])[-1] if s.get('lap_times') else 95.0 
                                    for s in drivers.values()])
        
        # Calculate traffic density
        driver_list = [{'id': did, 'position': s.get('position', 0), 'sector': 'S2'} 
                      for did, s in drivers.items()]
        traffic_density = self.traffic_model.calculate_traffic_density(driver_list, 'S2')
        
        # Simulate rejoin
        rejoin_result = self.pit_rejoin_sim.simulate_pit_rejoin(
            driver_id=state.get('driver_id', 'unknown'),
            current_position=current_position,
            pit_lap=lap,
            pit_time=total_pit_time,
            average_lap_time=average_lap_time,
            traffic_density=traffic_density,
            total_cars=total_cars,
            sector_at_pit='S2'
        )
        
        return {
            'lap': lap,
            'pit_time': total_pit_time,
            'new_compound': new_compound,
            'old_compound': current_compound,
            'rejoin_position': rejoin_result.get('rejoin_position', current_position),
            'positions_lost': rejoin_result.get('positions_lost', 0),
            'time_lost': rejoin_result.get('time_lost', total_pit_time),
            'traffic_impact': rejoin_result.get('traffic_impact', {})
        }
    
    def _simulate_overtakes(self, state: Dict, all_states: Dict, lap: int):
        """
        Simulate overtaking opportunities with proper probability model.
        """
        current_pos = state['position']
        if current_pos == 1:  # Leader can't overtake
            return
        
        # Find driver ahead
        ahead_driver = None
        for driver_id, s in all_states.items():
            if s['position'] == current_pos - 1:
                ahead_driver = (driver_id, s)
                break
        
        if not ahead_driver:
            return
        
        ahead_id, ahead_state = ahead_driver
        twin = state.get('twin', {})
        ahead_twin = ahead_state.get('twin', {})
        
        # Convert pace vector to speed estimate (for overtake model)
        # Pace vector: negative = faster, positive = slower
        base_speed = 150.0  # Base speed in km/h
        attacker_speed = base_speed * (1.0 - twin.get('pace_vector', 0.0) * 2)  # Convert pace to speed
        defender_speed = base_speed * (1.0 - ahead_twin.get('pace_vector', 0.0) * 2)
        
        # Determine current sector (rotate through sectors)
        sector = ['S1', 'S2', 'S3'][(lap - 1) % 3]
        
        # Calculate overtake probability using proper model
        overtake_prob = self.overtake_model.calculate_overtake_probability(
            attacker_speed=attacker_speed,
            defender_speed=defender_speed,
            attacker_position=current_pos,
            defender_position=current_pos - 1,
            attacker_tire_age=state.get('tire_age', 0),
            defender_tire_age=ahead_state.get('tire_age', 0),
            sector=sector
        )
        
        # Attempt overtake
        if np.random.random() < overtake_prob:
            # Successful overtake - swap positions
            state['position'], ahead_state['position'] = ahead_state['position'], state['position']
    
    def _calculate_traffic_penalty(
        self,
        driver_id: str,
        position: int,
        drivers: Dict,
        sector: str = 'S2'
    ) -> float:
        """
        Calculate time lost due to traffic using TrafficDensityModel.
        """
        # More cars ahead = more traffic
        cars_ahead = position - 1
        
        if cars_ahead == 0:
            return 0.0  # Leader has clean air
        
        # Convert drivers dict to list format for traffic model
        driver_list = [
            {'id': did, 'position': s.get('position', 0), 'sector': sector}
            for did, s in drivers.items()
        ]
        
        # Calculate traffic density
        traffic_density = self.traffic_model.calculate_traffic_density(
            drivers=driver_list,
            sector=sector
        )
        
        # Estimate time lost using traffic model
        time_lost = self.traffic_model.estimate_time_lost(
            traffic_density=traffic_density,
            sector=sector
        )
        
        # Additional penalty based on position (more cars ahead = more penalty)
        position_penalty = cars_ahead * 0.05  # 0.05s per car ahead
        
        total_penalty = time_lost + position_penalty
        
        # Add small random variation
        total_penalty += np.random.uniform(-0.02, 0.08)
        
        return max(total_penalty, 0.0)
    
    def _analyze_finishing_positions(self, simulation_results: List[Dict]) -> List[Dict]:
        """
        Analyze Monte Carlo results to get position probabilities.
        """
        # Count finishing positions for each driver
        driver_positions = {}
        
        for result in simulation_results:
            for pos, driver_id in enumerate(result['finishing_order'], 1):
                if driver_id not in driver_positions:
                    driver_positions[driver_id] = []
                driver_positions[driver_id].append(pos)
        
        # Calculate probabilities
        total_sims = len(simulation_results)
        finishing_probs = []
        
        for driver_id, positions in driver_positions.items():
            position_counter = Counter(positions)
            
            # Get most likely position
            most_common_pos = position_counter.most_common(1)[0][0]
            probability = position_counter[most_common_pos] / total_sims
            
            finishing_probs.append({
                'driver_id': driver_id,
                'position': most_common_pos,
                'probability': probability,
                'position_distribution': {
                    pos: count / total_sims
                    for pos, count in position_counter.items()
                }
            })
        
        # Sort by position
        finishing_probs.sort(key=lambda x: x['position'])
        
        return finishing_probs
    
    def _analyze_pit_strategies(self, simulation_results: List[Dict], drivers: List[Dict], 
                                driver_twins: Dict, current_lap: int, total_laps: int) -> Dict:
        """
        Analyze optimal pit strategies from simulations with undercut/overcut analysis.
        """
        # Find most common pit windows
        pit_windows = []
        for result in simulation_results:
            for driver_id, pits in result['pit_stops'].items():
                if pits:
                    for pit in pits:
                        pit_windows.append(pit['lap'])
        
        if not pit_windows:
            return {
                "optimal_window": {"start": 18, "end": 22},
                "undercut_viable": False,
                "time_gain": 0.0
            }
        
        # Find optimal window (most common pit lap ± 2 laps)
        most_common_pit = Counter(pit_windows).most_common(1)[0][0]
        optimal_start = max(1, most_common_pit - 2)
        optimal_end = most_common_pit + 2
        
        # Use StrategyOptimizer to analyze undercut/overcut for primary driver
        if drivers and len(drivers) > 0:
            primary_driver = drivers[0]
            driver_id = primary_driver.get('id', 'driver_1')
            twin = driver_twins.get(driver_id, {})
            
            # Get strategy optimization
            strategy_result = self.strategy_optimizer.optimize_pit_strategy(
                driver_id=driver_id,
                current_lap=current_lap,
                total_laps=total_laps,
                current_position=primary_driver.get('position', 1),
                tire_age=primary_driver.get('tire_age', 10),
                tire_compound=primary_driver.get('tire_compound', 'MEDIUM'),
                degradation_rate=twin.get('degradation_profile', {}).get('rate', 0.002),
                traffic_density=0.5,  # Average
                driver_pace=95.0,
                opponent_pace=95.5 if len(drivers) > 1 else None
            )
            
            undercut_analysis = strategy_result.get('undercut_analysis', {})
            overcut_analysis = strategy_result.get('overcut_analysis', {})
            
            return {
                "optimal_window": {
                    "start": optimal_start,
                    "end": optimal_end,
                    "most_common": most_common_pit
                },
                "undercut_viable": undercut_analysis.get('viable', False),
                "undercut_time_gain": undercut_analysis.get('time_gain', 0.0),
                "overcut_viable": overcut_analysis.get('viable', False),
                "overcut_time_gain": overcut_analysis.get('time_gain', 0.0),
                "recommendation": strategy_result.get('recommendation', {}),
                "pit_stops_per_driver": len(pit_windows) / len(simulation_results)
            }
        
        # Fallback
        return {
            "optimal_window": {
                "start": optimal_start,
                "end": optimal_end,
                "most_common": most_common_pit
            },
            "undercut_viable": False,
            "time_gain": 0.0,
            "pit_stops_per_driver": len(pit_windows) / len(simulation_results)
        }
    
    def _predict_tire_cliff(
        self,
        driver_twins: Dict,
        current_lap: int
    ) -> Dict:
        """
        Predict when tire performance will drop off significantly.
        """
        # Find earliest critical lap from all driver twins
        critical_laps = []
        for driver_id, twin in driver_twins.items():
            fatigue = twin.get('fatigue_dropoff', {})
            critical_lap = fatigue.get('critical_lap', current_lap + 20)
            critical_laps.append(critical_lap)
        
        if critical_laps:
            earliest_critical = min(critical_laps)
            return {
                "lap": earliest_critical,
                "critical": earliest_critical <= current_lap + 10
            }
        
        return {
            "lap": current_lap + 20,
            "critical": False
        }
    
    def _simulate_traffic_scenarios(self, simulation_results: List[Dict], drivers: List[Dict]) -> Dict:
        """
        Analyze traffic scenarios from simulations.
        """
        # Calculate average traffic density across simulations
        traffic_penalties = []
        clear_windows = []
        
        for result in simulation_results:
            # Estimate traffic from pit stop results
            for driver_id, pits in result.get('pit_stops', {}).items():
                for pit in pits:
                    traffic_impact = pit.get('traffic_impact', {})
                    if traffic_impact:
                        traffic_penalties.append(traffic_impact.get('traffic_loss_per_lap', 0.0))
                        clear_windows.append(traffic_impact.get('clear_window', True))
        
        avg_traffic_penalty = np.mean(traffic_penalties) if traffic_penalties else 0.2
        clear_window_ratio = sum(clear_windows) / len(clear_windows) if clear_windows else 0.5
        
        # Calculate current traffic density
        driver_list = [{'id': d.get('id'), 'position': d.get('position', 1), 'sector': 'S2'} 
                      for d in drivers]
        current_traffic = self.traffic_model.calculate_traffic_density(driver_list, 'S2')
        
        return {
            "clear_window": clear_window_ratio > 0.6,
            "busy": current_traffic > 0.7,
            "traffic_density": float(current_traffic),
            "average_traffic_penalty": float(avg_traffic_penalty),  # seconds per lap
            "clear_window_probability": float(clear_window_ratio)
        }
    
    def _analyze_undercut_outcomes(self, simulation_results: List[Dict], drivers: List[Dict], 
                                   driver_twins: Dict) -> Dict:
        """
        Analyze undercut/overcut outcomes from Monte Carlo simulations.
        """
        undercut_gains = []
        overcut_gains = []
        
        for result in simulation_results:
            # Analyze position changes from pit stops
            for driver_id, pits in result.get('pit_stops', {}).items():
                for pit in pits:
                    positions_lost = pit.get('positions_lost', 0)
                    # If positions lost is small, undercut might have worked
                    if positions_lost <= 1:
                        time_gain = pit.get('time_lost', 25.0) - 25.0  # Compare to base pit time
                        if time_gain < 0:  # Negative = time saved
                            undercut_gains.append(abs(time_gain))
        
        avg_undercut_gain = np.mean(undercut_gains) if undercut_gains else 0.0
        viable = avg_undercut_gain > 1.0
        
        return {
            "viable": viable,
            "time_gain": float(avg_undercut_gain),
            "confidence": "high" if avg_undercut_gain > 2.0 else "medium" if avg_undercut_gain > 1.0 else "low",
            "success_rate": len(undercut_gains) / max(len(simulation_results), 1) if undercut_gains else 0.0
        }
    
    def _generate_twin_from_driver(self, driver: Dict) -> Dict:
        """
        Generate or retrieve Driver Twin from driver data.
        """
        # If driver already has twin data, use it
        if 'twin' in driver:
            return driver['twin']
        
        # Otherwise generate from available data
        lap_times = driver.get('lap_times', [])
        sector_times = driver.get('sector_times', [])
        
        return self.driver_twin_gen.generate_driver_twin(
            driver_id=driver['id'],
            lap_times=lap_times,
            sector_times=sector_times,
            tire_compound=driver.get('tire_compound', 'MEDIUM'),
            current_lap=driver.get('current_lap', 0)
        )


def simulate_race_twin(
    race_id: str,
    drivers: List[Dict],
    total_laps: int,
    **kwargs
) -> Dict:
    """
    Convenience function to simulate Race Twin.
    """
    simulator = RaceTwinSimulator(num_simulations=kwargs.get('num_simulations', 500))
    return simulator.simulate_race(race_id, drivers, total_laps, **kwargs)


if __name__ == "__main__":
    # Test Race Twin simulation
    simulator = RaceTwinSimulator(num_simulations=100)
    
    drivers = [
        {
            'id': 'driver_1',
            'position': 1,
            'lap_times': [95.234, 95.456, 95.123],
            'sector_times': [{"S1": 31.5, "S2": 32.0, "S3": 31.7}],
            'tire_age': 10,
            'tire_compound': 'MEDIUM'
        },
        {
            'id': 'driver_2',
            'position': 2,
            'lap_times': [95.567, 95.678, 95.789],
            'sector_times': [{"S1": 31.8, "S2": 32.2, "S3": 31.8}],
            'tire_age': 8,
            'tire_compound': 'SOFT'
        }
    ]
    
    race_twin = simulator.simulate_race(
        race_id="race_1",
        drivers=drivers,
        total_laps=50,
        current_lap=10
    )
    
    print(json.dumps(race_twin, indent=2))

