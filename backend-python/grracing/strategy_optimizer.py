"""
Strategy Optimizer

Optimizes pit strategy with undercut/overcut modeling and degradation-aware decisions.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .degradation import TireDegradationModel
from .pit_rejoin import PitRejoinSimulator
from .traffic import TrafficDensityModel


class StrategyOptimizer:
    """
    Optimizes race strategy including:
    - Best lap to pit
    - Undercut vs overcut modeling
    - Degradation-aware decision engine
    """
    
    def __init__(self):
        self.degradation_model = TireDegradationModel()
        self.pit_rejoin_sim = PitRejoinSimulator()
        self.traffic_model = TrafficDensityModel()
        
    def optimize_pit_strategy(
        self,
        driver_id: str,
        current_lap: int,
        total_laps: int,
        current_position: int,
        tire_age: int,
        tire_compound: str,
        degradation_rate: float,
        traffic_density: float,
        driver_pace: float,
        opponent_pace: Optional[float] = None
    ) -> Dict:
        """
        Optimize pit strategy for a driver.
        
        Returns:
            Optimal pit strategy with undercut/overcut analysis
        """
        # Calculate optimal pit window
        optimal_window = self._calculate_optimal_pit_window(
            current_lap=current_lap,
            total_laps=total_laps,
            tire_age=tire_age,
            degradation_rate=degradation_rate,
            traffic_density=traffic_density
        )
        
        # Analyze undercut opportunity
        undercut_analysis = self._analyze_undercut(
            driver_id=driver_id,
            current_lap=current_lap,
            optimal_window=optimal_window,
            driver_pace=driver_pace,
            opponent_pace=opponent_pace,
            tire_age=tire_age,
            traffic_density=traffic_density
        )
        
        # Analyze overcut opportunity
        overcut_analysis = self._analyze_overcut(
            driver_id=driver_id,
            current_lap=current_lap,
            optimal_window=optimal_window,
            driver_pace=driver_pace,
            opponent_pace=opponent_pace,
            tire_age=tire_age,
            traffic_density=traffic_density
        )
        
        # Degradation-aware decision
        degradation_decision = self._make_degradation_aware_decision(
            tire_age=tire_age,
            degradation_rate=degradation_rate,
            optimal_window=optimal_window,
            current_lap=current_lap
        )
        
        # Risk scoring
        risk_score = self._calculate_risk_score(
            tire_age=tire_age,
            degradation_rate=degradation_rate,
            traffic_density=traffic_density,
            position=current_position
        )
        
        return {
            "driver_id": driver_id,
            "current_lap": current_lap,
            "optimal_pit_window": optimal_window,
            "undercut_analysis": undercut_analysis,
            "overcut_analysis": overcut_analysis,
            "degradation_decision": degradation_decision,
            "risk_score": risk_score,
            "recommendation": self._generate_recommendation(
                undercut_analysis,
                overcut_analysis,
                degradation_decision,
                risk_score
            ),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _calculate_optimal_pit_window(
        self,
        current_lap: int,
        total_laps: int,
        tire_age: int,
        degradation_rate: float,
        traffic_density: float
    ) -> Dict:
        """
        Calculate optimal pit window considering degradation and traffic.
        """
        # Base optimal window (when degradation becomes significant)
        degradation_threshold = 0.02  # 2% pace loss
        critical_lap = current_lap + int(degradation_threshold / degradation_rate) if degradation_rate > 0 else current_lap + 20
        
        # Adjust for traffic (avoid pitting in heavy traffic)
        traffic_adjustment = 0
        if traffic_density > 0.7:
            traffic_adjustment = -2  # Pit earlier to avoid traffic
        elif traffic_density < 0.3:
            traffic_adjustment = 2  # Can wait for better window
        
        optimal_lap = max(current_lap + 1, min(critical_lap + traffic_adjustment, total_laps - 10))
        
        return {
            "start": max(current_lap + 1, optimal_lap - 2),
            "end": min(total_laps - 5, optimal_lap + 2),
            "optimal": optimal_lap,
            "urgency": "high" if tire_age > 20 else "medium" if tire_age > 15 else "low"
        }
    
    def _analyze_undercut(
        self,
        driver_id: str,
        current_lap: int,
        optimal_window: Dict,
        driver_pace: float,
        opponent_pace: Optional[float],
        tire_age: int,
        traffic_density: float
    ) -> Dict:
        """
        Analyze undercut opportunity (pit early, gain on fresh tires).
        """
        if not opponent_pace:
            opponent_pace = driver_pace  # Assume similar pace
        
        # Undercut works if:
        # 1. Driver is behind opponent
        # 2. Fresh tires provide pace advantage
        # 3. Traffic window is clear
        
        # Calculate pace advantage with fresh tires
        fresh_tire_advantage = 0.015  # ~1.5% faster with fresh tires
        pace_gain_per_lap = driver_pace * fresh_tire_advantage
        
        # Estimate laps until opponent pits
        opponent_pit_lap = optimal_window["optimal"] + 3  # Opponent likely pits later
        
        # Calculate undercut window
        undercut_lap = max(current_lap + 1, optimal_window["start"] - 2)
        laps_undercut = opponent_pit_lap - undercut_lap
        
        if laps_undercut <= 0:
            return {
                "viable": False,
                "reason": "Opponent will pit before or at same time",
                "time_gain": 0.0
            }
        
        # Calculate total time gain
        total_gain = pace_gain_per_lap * laps_undercut
        
        # Traffic penalty
        traffic_penalty = traffic_density * 0.5  # Up to 0.5s lost in traffic
        net_gain = total_gain - traffic_penalty
        
        # Undercut is viable if net gain > 1 second
        viable = net_gain > 1.0 and traffic_density < 0.5
        
        return {
            "viable": viable,
            "recommended_lap": undercut_lap if viable else optimal_window["optimal"],
            "time_gain": max(0.0, net_gain),
            "laps_undercut": laps_undercut,
            "traffic_impact": traffic_penalty,
            "confidence": "high" if net_gain > 2.0 else "medium" if net_gain > 1.0 else "low"
        }
    
    def _analyze_overcut(
        self,
        driver_id: str,
        current_lap: int,
        optimal_window: Dict,
        driver_pace: float,
        opponent_pace: Optional[float],
        tire_age: int,
        traffic_density: float
    ) -> Dict:
        """
        Analyze overcut opportunity (pit later, opponent's tires degrade first).
        """
        if not opponent_pace:
            opponent_pace = driver_pace
        
        # Overcut works if:
        # 1. Driver can extend stint longer than opponent
        # 2. Opponent's tires degrade significantly
        # 3. Driver maintains pace better
        
        # Estimate when opponent will pit
        opponent_pit_lap = optimal_window["optimal"] + 2
        
        # Overcut window (pit after opponent)
        overcut_lap = opponent_pit_lap + 3
        
        if overcut_lap > optimal_window["end"]:
            return {
                "viable": False,
                "reason": "Overcut window exceeds optimal pit window",
                "time_gain": 0.0
            }
        
        # Calculate time gain from opponent's tire degradation
        opponent_tire_age_at_pit = opponent_pit_lap - current_lap + tire_age
        degradation_penalty = opponent_tire_age_at_pit * 0.002  # 0.2% per lap
        
        # Driver maintains pace (tires still good)
        driver_advantage = degradation_penalty * 3  # 3 laps of advantage
        
        # Traffic consideration
        traffic_penalty = traffic_density * 0.3
        net_gain = driver_advantage - traffic_penalty
        
        viable = net_gain > 0.5 and tire_age < 18  # Can extend stint
        
        return {
            "viable": viable,
            "recommended_lap": overcut_lap if viable else optimal_window["optimal"],
            "time_gain": max(0.0, net_gain),
            "opponent_degradation": degradation_penalty,
            "traffic_impact": traffic_penalty,
            "confidence": "high" if net_gain > 1.5 else "medium" if net_gain > 0.5 else "low"
        }
    
    def _make_degradation_aware_decision(
        self,
        tire_age: int,
        degradation_rate: float,
        optimal_window: Dict,
        current_lap: int
    ) -> Dict:
        """
        Make pit decision based on degradation curve.
        """
        # Calculate current degradation
        current_degradation = tire_age * degradation_rate
        
        # Predict degradation at optimal window
        laps_to_window = optimal_window["optimal"] - current_lap
        future_degradation = (tire_age + laps_to_window) * degradation_rate
        
        # Decision logic
        if current_degradation > 0.05:  # 5% degradation
            decision = "PIT_NOW"
            urgency = "critical"
        elif future_degradation > 0.04:  # Will reach 4% at window
            decision = "PIT_IN_WINDOW"
            urgency = "high"
        elif degradation_rate > 0.003:  # High degradation rate
            decision = "PIT_EARLY"
            urgency = "medium"
        else:
            decision = "EXTEND_STINT"
            urgency = "low"
        
        return {
            "decision": decision,
            "urgency": urgency,
            "current_degradation": current_degradation,
            "predicted_degradation": future_degradation,
            "degradation_rate": degradation_rate
        }
    
    def _calculate_risk_score(
        self,
        tire_age: int,
        degradation_rate: float,
        traffic_density: float,
        position: int
    ) -> Dict:
        """
        Calculate risk score for current strategy.
        """
        risks = []
        score = 0.0
        
        # Tire age risk
        if tire_age > 25:
            risks.append("Critical tire age - high failure risk")
            score += 0.4
        elif tire_age > 20:
            risks.append("High tire age - performance degradation")
            score += 0.3
        
        # Degradation risk
        if degradation_rate > 0.004:
            risks.append("High degradation rate - pace loss accelerating")
            score += 0.3
        
        # Traffic risk
        if traffic_density > 0.7:
            risks.append("Heavy traffic - difficult pit rejoin")
            score += 0.2
        
        # Position risk
        if position <= 3:
            risks.append("Podium position - strategy critical")
            score += 0.1
        
        return {
            "score": min(1.0, score),  # Normalize to 0-1
            "level": "high" if score > 0.6 else "medium" if score > 0.3 else "low",
            "risks": risks
        }
    
    def _generate_recommendation(
        self,
        undercut: Dict,
        overcut: Dict,
        degradation: Dict,
        risk: Dict
    ) -> Dict:
        """
        Generate final strategy recommendation.
        """
        # Prioritize based on opportunities
        if undercut["viable"] and undercut["time_gain"] > 2.0:
            return {
                "strategy": "UNDERCUT",
                "lap": undercut["recommended_lap"],
                "reasoning": f"Strong undercut opportunity - {undercut['time_gain']:.2f}s potential gain",
                "confidence": undercut["confidence"]
            }
        
        if overcut["viable"] and overcut["time_gain"] > 1.5:
            return {
                "strategy": "OVERCUT",
                "lap": overcut["recommended_lap"],
                "reasoning": f"Overcut viable - opponent tires degrading, {overcut['time_gain']:.2f}s gain",
                "confidence": overcut["confidence"]
            }
        
        # Default to degradation-based decision
        if degradation["decision"] == "PIT_NOW":
            return {
                "strategy": "PIT_NOW",
                "lap": None,
                "reasoning": "Critical degradation - pit immediately",
                "confidence": "high"
            }
        
        return {
            "strategy": "STANDARD_PIT",
            "lap": degradation.get("optimal_lap", None),
            "reasoning": "Follow standard pit window strategy",
            "confidence": "medium"
        }


def optimize_strategy(
    driver_id: str,
    current_lap: int,
    **kwargs
) -> Dict:
    """
    Convenience function to optimize strategy.
    """
    optimizer = StrategyOptimizer()
    return optimizer.optimize_pit_strategy(
        driver_id=driver_id,
        current_lap=current_lap,
        **kwargs
    )


if __name__ == "__main__":
    # Test strategy optimizer
    optimizer = StrategyOptimizer()
    
    result = optimizer.optimize_pit_strategy(
        driver_id="driver_1",
        current_lap=15,
        total_laps=50,
        current_position=5,
        tire_age=18,
        tire_compound="MEDIUM",
        degradation_rate=0.0025,
        traffic_density=0.4,
        driver_pace=95.0,
        opponent_pace=95.5
    )
    
    print("Strategy Optimization:")
    print(result)

