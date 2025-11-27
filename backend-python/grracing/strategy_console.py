"""
Strategy Console Backend Logic

Provides advanced strategy analysis including:
- Dynamic pit window timeline
- Undercut/overcut simulation
- Risk scoring algorithm
- Tire life prediction
- Rejoin window calculation
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .degradation import TireDegradationModel
from .pit_rejoin import PitRejoinSimulator
from .strategy_optimizer import StrategyOptimizer
from .traffic import TrafficDensityModel


class StrategyConsoleEngine:
    """
    Advanced strategy console engine for real-time race analysis.
    """
    
    def __init__(self):
        self.degradation_model = TireDegradationModel()
        self.pit_rejoin_sim = PitRejoinSimulator()
        self.strategy_optimizer = StrategyOptimizer()
        self.traffic_model = TrafficDensityModel()
    
    def generate_pit_window_timeline(
        self,
        driver_id: str,
        current_lap: int,
        total_laps: int,
        tire_age: int,
        tire_compound: str,
        degradation_rate: float,
        current_position: int,
        traffic_density: float
    ) -> Dict:
        """
        Generate dynamic pit window timeline showing optimal pit windows across the race.
        
        Returns timeline with:
        - Recommended pit windows (start, end, optimal lap)
        - Tire life predictions per window
        - Traffic density per window
        - Risk scores per window
        """
        timeline = []
        
        # Calculate optimal pit windows (typically 2-3 stops for a race)
        num_stops = self._estimate_num_stops(total_laps, tire_compound)
        laps_per_stint = total_laps // (num_stops + 1)
        
        for stop_num in range(num_stops):
            window_start = max(current_lap, (stop_num + 1) * laps_per_stint - 3)
            window_end = min(total_laps, (stop_num + 1) * laps_per_stint + 3)
            optimal_lap = (window_start + window_end) // 2
            
            # Predict tire life at this window
            tire_age_at_window = tire_age + (optimal_lap - current_lap)
            tire_life_remaining = self._predict_tire_life(
                tire_age_at_window,
                tire_compound,
                degradation_rate
            )
            
            # Estimate traffic density at this window
            predicted_traffic = self._predict_traffic_at_lap(
                optimal_lap,
                current_lap,
                traffic_density,
                total_laps
            )
            
            # Calculate risk score for this window
            risk_score = self._calculate_window_risk(
                tire_age_at_window,
                degradation_rate,
                predicted_traffic,
                optimal_lap,
                total_laps
            )
            
            timeline.append({
                "stop_number": stop_num + 1,
                "window": {
                    "start": window_start,
                    "end": window_end,
                    "optimal": optimal_lap
                },
                "tire_life": {
                    "age_at_window": tire_age_at_window,
                    "remaining_laps": tire_life_remaining,
                    "compound": tire_compound,
                    "degradation_rate": degradation_rate
                },
                "traffic": {
                    "density": predicted_traffic,
                    "level": "high" if predicted_traffic > 0.7 else "medium" if predicted_traffic > 0.4 else "low"
                },
                "risk": risk_score,
                "recommendation": self._get_window_recommendation(risk_score, tire_life_remaining)
            })
        
        return {
            "driver_id": driver_id,
            "current_lap": current_lap,
            "total_laps": total_laps,
            "timeline": timeline,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def simulate_undercut_overcut(
        self,
        driver_id: str,
        current_lap: int,
        driver_pace: float,
        opponent_pace: Optional[float],
        tire_age: int,
        opponent_tire_age: int,
        degradation_rate: float,
        traffic_density: float,
        current_position: int,
        opponent_position: int
    ) -> Dict:
        """
        Simulate undercut and overcut scenarios with detailed analysis.
        
        Returns:
        - Undercut simulation (pit early)
        - Overcut simulation (pit late)
        - Time gains/losses
        - Position changes
        - Risk assessment
        """
        if not opponent_pace:
            opponent_pace = driver_pace
        
        # Get strategy optimization
        strategy_result = self.strategy_optimizer.optimize_pit_strategy(
            driver_id=driver_id,
            current_lap=current_lap,
            total_laps=50,  # Default
            current_position=current_position,
            tire_age=tire_age,
            tire_compound="MEDIUM",
            degradation_rate=degradation_rate,
            traffic_density=traffic_density,
            driver_pace=driver_pace,
            opponent_pace=opponent_pace
        )
        
        undercut_analysis = strategy_result.get('undercut_analysis', {})
        overcut_analysis = strategy_result.get('overcut_analysis', {})
        
        # Simulate undercut scenario
        undercut_simulation = self._simulate_undercut_scenario(
            driver_pace=driver_pace,
            opponent_pace=opponent_pace,
            tire_age=tire_age,
            opponent_tire_age=opponent_tire_age,
            degradation_rate=degradation_rate,
            traffic_density=traffic_density,
            current_position=current_position,
            opponent_position=opponent_position,
            analysis=undercut_analysis
        )
        
        # Simulate overcut scenario
        overcut_simulation = self._simulate_overcut_scenario(
            driver_pace=driver_pace,
            opponent_pace=opponent_pace,
            tire_age=tire_age,
            opponent_tire_age=opponent_tire_age,
            degradation_rate=degradation_rate,
            traffic_density=traffic_density,
            current_position=current_position,
            opponent_position=opponent_position,
            analysis=overcut_analysis
        )
        
        return {
            "driver_id": driver_id,
            "current_lap": current_lap,
            "undercut": undercut_simulation,
            "overcut": overcut_simulation,
            "recommendation": self._compare_strategies(undercut_simulation, overcut_simulation),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def calculate_risk_score(
        self,
        tire_age: int,
        degradation_rate: float,
        traffic_density: float,
        position: int,
        laps_remaining: int,
        tire_compound: str
    ) -> Dict:
        """
        Calculate comprehensive risk score for current strategy.
        
        Returns detailed risk breakdown with scores and recommendations.
        """
        risks = []
        risk_factors = {}
        total_score = 0.0
        
        # Tire age risk
        tire_risk = self._calculate_tire_risk(tire_age, tire_compound)
        risk_factors["tire_age"] = tire_risk
        total_score += tire_risk["score"]
        if tire_risk["score"] > 0.3:
            risks.append(tire_risk["description"])
        
        # Degradation risk
        degradation_risk = self._calculate_degradation_risk(degradation_rate)
        risk_factors["degradation"] = degradation_risk
        total_score += degradation_risk["score"]
        if degradation_risk["score"] > 0.3:
            risks.append(degradation_risk["description"])
        
        # Traffic risk
        traffic_risk = self._calculate_traffic_risk(traffic_density, position)
        risk_factors["traffic"] = traffic_risk
        total_score += traffic_risk["score"]
        if traffic_risk["score"] > 0.3:
            risks.append(traffic_risk["description"])
        
        # Position risk
        position_risk = self._calculate_position_risk(position, laps_remaining)
        risk_factors["position"] = position_risk
        total_score += position_risk["score"]
        if position_risk["score"] > 0.3:
            risks.append(position_risk["description"])
        
        # Normalize total score
        total_score = min(1.0, total_score / 4.0)  # Average of 4 factors
        
        return {
            "total_score": float(total_score),
            "risk_level": "high" if total_score > 0.7 else "medium" if total_score > 0.4 else "low",
            "risk_factors": risk_factors,
            "risks": risks,
            "recommendation": self._get_risk_recommendation(total_score, risk_factors),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def predict_tire_life(
        self,
        tire_age: int,
        tire_compound: str,
        degradation_rate: float,
        track_temperature: float = 25.0,
        driver_aggression: float = 0.5
    ) -> Dict:
        """
        Predict remaining tire life based on current conditions.
        
        Returns:
        - Remaining laps until tire cliff
        - Predicted degradation curve
        - Critical lap prediction
        - Confidence score
        """
        # Base tire life by compound
        compound_lifespan = {
            "SOFT": 15,
            "MEDIUM": 25,
            "HARD": 35
        }
        base_lifespan = compound_lifespan.get(tire_compound, 25)
        
        # Adjust for degradation rate
        degradation_multiplier = 1.0 - (degradation_rate * 100)  # Higher rate = shorter life
        adjusted_lifespan = base_lifespan * degradation_multiplier
        
        # Adjust for temperature (higher temp = faster degradation)
        temp_factor = 1.0 + ((track_temperature - 25.0) / 50.0) * 0.2
        adjusted_lifespan /= temp_factor
        
        # Adjust for driver aggression
        aggression_factor = 1.0 - (driver_aggression * 0.1)  # More aggressive = shorter life
        adjusted_lifespan *= aggression_factor
        
        # Remaining life
        remaining_laps = max(0, adjusted_lifespan - tire_age)
        
        # Critical lap (when tire cliff likely)
        critical_lap = tire_age + int(remaining_laps * 0.8)  # 80% of remaining life
        
        # Generate degradation curve
        degradation_curve = []
        for lap_offset in range(0, min(20, int(remaining_laps) + 5)):
            lap = tire_age + lap_offset
            if lap <= adjusted_lifespan:
                # Exponential degradation
                degradation = degradation_rate * lap * (1 + lap * 0.01)
                degradation_curve.append({
                    "lap": lap,
                    "degradation": float(degradation),
                    "pace_loss": float(degradation * 0.5)  # Convert to pace loss
                })
        
        # Confidence based on data quality
        confidence = 0.9 if degradation_rate > 0 else 0.5
        
        return {
            "tire_age": tire_age,
            "tire_compound": tire_compound,
            "remaining_laps": int(remaining_laps),
            "critical_lap": int(critical_lap),
            "degradation_curve": degradation_curve,
            "confidence": float(confidence),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def calculate_rejoin_window(
        self,
        driver_id: str,
        current_position: int,
        pit_lap: int,
        traffic_density: float,
        total_cars: int,
        sector_at_pit: str = "S2"
    ) -> Dict:
        """
        Calculate optimal rejoin window after pit stop.
        
        Returns:
        - Rejoin position prediction
        - Traffic impact analysis
        - Clear window detection
        - Time lost estimation
        - Ghost driver comparison
        """
        # Use pit rejoin simulator
        rejoin_result = self.pit_rejoin_sim.simulate_pit_rejoin(
            driver_id=driver_id,
            current_position=current_position,
            pit_lap=pit_lap,
            pit_time=22.0,  # Default pit time
            average_lap_time=95.0,  # Default
            traffic_density=traffic_density,
            total_cars=total_cars,
            sector_at_pit=sector_at_pit
        )
        
        # Calculate clear window
        clear_window = self._detect_clear_window(
            rejoin_position=rejoin_result["rejoin_position"],
            traffic_density=traffic_density,
            total_cars=total_cars
        )
        
        # Estimate time lost
        time_lost = rejoin_result["time_lost"]
        
        return {
            "driver_id": driver_id,
            "pit_lap": pit_lap,
            "rejoin": {
                "position": rejoin_result["rejoin_position"],
                "positions_lost": rejoin_result["positions_lost"],
                "time_lost": time_lost,
                "sector": rejoin_result["rejoin_sector"]
            },
            "traffic": {
                "density": traffic_density,
                "impact": rejoin_result["traffic_impact"],
                "clear_window": clear_window
            },
            "ghost": {
                "position": rejoin_result["ghost_position"],
                "advantage": rejoin_result["position_before_pit"] - rejoin_result["ghost_position"]
            },
            "recommendation": "PIT_NOW" if clear_window else "WAIT_FOR_CLEAR_WINDOW",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    # Helper methods
    
    def _estimate_num_stops(self, total_laps: int, compound: str) -> int:
        """Estimate number of pit stops needed."""
        compound_stint_length = {"SOFT": 15, "MEDIUM": 25, "HARD": 35}
        stint_length = compound_stint_length.get(compound, 25)
        return max(1, (total_laps // stint_length) - 1)
    
    def _predict_tire_life(self, tire_age: int, compound: str, degradation_rate: float) -> int:
        """Predict remaining tire life in laps."""
        compound_lifespan = {"SOFT": 15, "MEDIUM": 25, "HARD": 35}
        base_lifespan = compound_lifespan.get(compound, 25)
        remaining = base_lifespan - tire_age
        # Adjust for degradation rate
        remaining = int(remaining * (1.0 - degradation_rate * 50))
        return max(0, remaining)
    
    def _predict_traffic_at_lap(self, lap: int, current_lap: int, current_density: float, total_laps: int) -> float:
        """Predict traffic density at a future lap."""
        # Traffic typically decreases as field spreads out
        progress = (lap - current_lap) / max(1, total_laps - current_lap)
        predicted = current_density * (1.0 - progress * 0.3)  # 30% reduction over race
        return max(0.0, min(1.0, predicted))
    
    def _calculate_window_risk(self, tire_age: int, degradation_rate: float, traffic: float, lap: int, total_laps: int) -> Dict:
        """Calculate risk score for a pit window."""
        score = 0.0
        risks = []
        
        if tire_age > 25:
            score += 0.4
            risks.append("High tire age")
        if degradation_rate > 0.004:
            score += 0.3
            risks.append("High degradation rate")
        if traffic > 0.7:
            score += 0.2
            risks.append("Heavy traffic")
        if lap > total_laps * 0.8:
            score += 0.1
            risks.append("Late in race")
        
        return {
            "score": min(1.0, score),
            "level": "high" if score > 0.6 else "medium" if score > 0.3 else "low",
            "risks": risks
        }
    
    def _get_window_recommendation(self, risk: Dict, tire_life: int) -> str:
        """Get recommendation for pit window."""
        if risk["level"] == "high":
            return "AVOID"
        if tire_life < 5:
            return "URGENT"
        if risk["level"] == "medium":
            return "CAUTION"
        return "RECOMMENDED"
    
    def _simulate_undercut_scenario(self, **kwargs) -> Dict:
        """Simulate undercut scenario."""
        analysis = kwargs.get("analysis", {})
        return {
            "viable": analysis.get("viable", False),
            "recommended_lap": analysis.get("recommended_lap", 0),
            "time_gain": analysis.get("time_gain", 0.0),
            "position_gain": 1 if analysis.get("time_gain", 0) > 2.0 else 0,
            "confidence": analysis.get("confidence", "low"),
            "risks": ["Traffic on rejoin", "Opponent may respond"] if analysis.get("viable") else []
        }
    
    def _simulate_overcut_scenario(self, **kwargs) -> Dict:
        """Simulate overcut scenario."""
        analysis = kwargs.get("analysis", {})
        return {
            "viable": analysis.get("viable", False),
            "recommended_lap": analysis.get("recommended_lap", 0),
            "time_gain": analysis.get("time_gain", 0.0),
            "position_gain": 1 if analysis.get("time_gain", 0) > 1.5 else 0,
            "confidence": analysis.get("confidence", "low"),
            "risks": ["Tire degradation", "Opponent may undercut"] if analysis.get("viable") else []
        }
    
    def _compare_strategies(self, undercut: Dict, overcut: Dict) -> Dict:
        """Compare undercut vs overcut strategies."""
        if undercut["viable"] and undercut["time_gain"] > overcut.get("time_gain", 0):
            return {
                "strategy": "UNDERCUT",
                "reasoning": f"Undercut offers {undercut['time_gain']:.2f}s gain",
                "confidence": undercut["confidence"]
            }
        elif overcut["viable"]:
            return {
                "strategy": "OVERCUT",
                "reasoning": f"Overcut offers {overcut['time_gain']:.2f}s gain",
                "confidence": overcut["confidence"]
            }
        return {
            "strategy": "STANDARD",
            "reasoning": "No significant advantage from undercut/overcut",
            "confidence": "medium"
        }
    
    def _calculate_tire_risk(self, tire_age: int, compound: str) -> Dict:
        """Calculate tire age risk."""
        compound_max = {"SOFT": 20, "MEDIUM": 30, "HARD": 40}
        max_age = compound_max.get(compound, 30)
        
        if tire_age > max_age * 0.9:
            return {"score": 0.5, "level": "high", "description": f"Critical tire age ({tire_age} laps)"}
        elif tire_age > max_age * 0.7:
            return {"score": 0.3, "level": "medium", "description": f"High tire age ({tire_age} laps)"}
        return {"score": 0.1, "level": "low", "description": f"Normal tire age ({tire_age} laps)"}
    
    def _calculate_degradation_risk(self, degradation_rate: float) -> Dict:
        """Calculate degradation risk."""
        if degradation_rate > 0.004:
            return {"score": 0.4, "level": "high", "description": f"High degradation rate ({degradation_rate:.4f})"}
        elif degradation_rate > 0.002:
            return {"score": 0.2, "level": "medium", "description": f"Moderate degradation rate ({degradation_rate:.4f})"}
        return {"score": 0.1, "level": "low", "description": f"Low degradation rate ({degradation_rate:.4f})"}
    
    def _calculate_traffic_risk(self, traffic_density: float, position: int) -> Dict:
        """Calculate traffic risk."""
        if traffic_density > 0.7:
            return {"score": 0.3, "level": "high", "description": f"Heavy traffic (density: {traffic_density:.2f})"}
        elif traffic_density > 0.4:
            return {"score": 0.2, "level": "medium", "description": f"Moderate traffic (density: {traffic_density:.2f})"}
        return {"score": 0.1, "level": "low", "description": f"Clear traffic (density: {traffic_density:.2f})"}
    
    def _calculate_position_risk(self, position: int, laps_remaining: int) -> Dict:
        """Calculate position risk."""
        if position <= 3 and laps_remaining < 10:
            return {"score": 0.3, "level": "high", "description": "Podium position - strategy critical"}
        elif position <= 5:
            return {"score": 0.2, "level": "medium", "description": "Top 5 position - important"}
        return {"score": 0.1, "level": "low", "description": f"Position {position} - standard risk"}
    
    def _get_risk_recommendation(self, total_score: float, risk_factors: Dict) -> str:
        """Get recommendation based on risk score."""
        if total_score > 0.7:
            return "PIT_IMMEDIATELY"
        elif total_score > 0.4:
            return "PIT_SOON"
        return "MONITOR"
    
    def _detect_clear_window(self, rejoin_position: int, traffic_density: float, total_cars: int) -> bool:
        """Detect if there's a clear window for rejoin."""
        # Clear window if low traffic and good rejoin position
        return traffic_density < 0.4 and rejoin_position < total_cars * 0.7

