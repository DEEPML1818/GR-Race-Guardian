"""
Advanced Pit Decision Engine

Multi-factor decision engine that considers:
- Tire degradation (current and predicted)
- Traffic conditions and windows
- Race Twin simulation outcomes
- Confidence scoring system
- Detailed factor breakdown JSON
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .degradation import TireDegradationModel
from .traffic import TrafficDensityModel
from .strategy_optimizer import StrategyOptimizer
from .pit_rejoin import PitRejoinSimulator


class AdvancedPitDecisionEngine:
    """
    Advanced pit decision engine with multi-factor analysis.
    
    Features:
    - Multi-factor decision engine (degradation, traffic, raceTwin)
    - Confidence scoring system (0-1 scale)
    - Factor breakdown explanation JSON
    - Integration with Race Twin simulator
    """
    
    def __init__(self):
        self.degradation_model = TireDegradationModel()
        self.traffic_model = TrafficDensityModel()
        self.strategy_optimizer = StrategyOptimizer()
        self.pit_rejoin_sim = PitRejoinSimulator()
        
    def make_pit_decision(
        self,
        driver_id: str,
        current_lap: int,
        total_laps: int,
        tire_age: int,
        tire_compound: str,
        current_position: int,
        degradation_rate: float,
        traffic_density: float,
        race_twin: Optional[Dict] = None,
        driver_twin: Optional[Dict] = None,
        opponent_data: Optional[List[Dict]] = None,
        weather_data: Optional[Dict] = None
    ) -> Dict:
        """
        Make advanced pit decision with multi-factor analysis.
        
        Returns:
            Complete decision JSON with:
            - decision: PIT_NOW, PIT_LATER, EXTEND_STINT
            - confidence: 0.0-1.0 score
            - factor_breakdown: Detailed analysis of each factor
            - reasoning: Human-readable explanation
            - race_twin_integration: Race Twin insights
        """
        # 1. Degradation Factor Analysis
        degradation_factor = self._analyze_degradation_factor(
            tire_age=tire_age,
            tire_compound=tire_compound,
            degradation_rate=degradation_rate,
            current_lap=current_lap,
            total_laps=total_laps,
            driver_twin=driver_twin
        )
        
        # 2. Traffic Factor Analysis
        traffic_factor = self._analyze_traffic_factor(
            current_position=current_position,
            traffic_density=traffic_density,
            current_lap=current_lap,
            total_laps=total_laps,
            driver_id=driver_id
        )
        
        # 3. Race Twin Factor Analysis
        race_twin_factor = self._analyze_race_twin_factor(
            race_twin=race_twin,
            driver_id=driver_id,
            current_lap=current_lap,
            total_laps=total_laps
        )
        
        # 4. Opponent Strategy Factor
        opponent_factor = self._analyze_opponent_factor(
            opponent_data=opponent_data,
            current_lap=current_lap,
            tire_age=tire_age,
            driver_id=driver_id
        )
        
        # 5. Weather Factor
        weather_factor = self._analyze_weather_factor(
            weather_data=weather_data,
            tire_compound=tire_compound
        )
        
        # 6. Calculate Confidence Score
        confidence_score = self._calculate_confidence_score(
            degradation_factor=degradation_factor,
            traffic_factor=traffic_factor,
            race_twin_factor=race_twin_factor,
            opponent_factor=opponent_factor,
            weather_factor=weather_factor
        )
        
        # 7. Make Decision
        decision_result = self._make_decision(
            degradation_factor=degradation_factor,
            traffic_factor=traffic_factor,
            race_twin_factor=race_twin_factor,
            opponent_factor=opponent_factor,
            weather_factor=weather_factor,
            confidence_score=confidence_score,
            current_lap=current_lap,
            total_laps=total_laps,
            tire_age=tire_age
        )
        
        # 8. Generate Factor Breakdown
        factor_breakdown = self._generate_factor_breakdown(
            degradation_factor=degradation_factor,
            traffic_factor=traffic_factor,
            race_twin_factor=race_twin_factor,
            opponent_factor=opponent_factor,
            weather_factor=weather_factor,
            confidence_score=confidence_score
        )
        
        return {
            "driver_id": driver_id,
            "current_lap": current_lap,
            "decision": decision_result["decision"],
            "confidence": confidence_score,
            "confidence_level": self._confidence_level(confidence_score),
            "factor_breakdown": factor_breakdown,
            "reasoning": decision_result["reasoning"],
            "recommended_lap": decision_result.get("recommended_lap"),
            "race_twin_integration": race_twin_factor.get("insights", {}),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _analyze_degradation_factor(
        self,
        tire_age: int,
        tire_compound: str,
        degradation_rate: float,
        current_lap: int,
        total_laps: int,
        driver_twin: Optional[Dict]
    ) -> Dict:
        """Analyze tire degradation factor."""
        # Calculate current degradation
        degradation_model = TireDegradationModel(compound=tire_compound)
        current_degradation = degradation_model.calculate_degradation(
            tire_age=tire_age,
            compound=tire_compound
        )
        
        # Predict degradation for next 5 laps
        predicted_degradation = []
        for lap_offset in range(1, 6):
            future_age = tire_age + lap_offset
            future_degradation = degradation_model.calculate_degradation(
                tire_age=future_age,
                compound=tire_compound
            )
            predicted_degradation.append({
                "lap": current_lap + lap_offset,
                "degradation": float(future_degradation),
                "pace_loss": float(future_degradation * 0.5)  # Convert to pace loss
            })
        
        # Determine degradation urgency
        critical_threshold = 0.05  # 5% degradation
        warning_threshold = 0.03   # 3% degradation
        
        if current_degradation >= critical_threshold:
            urgency = "critical"
            score = 0.9
        elif current_degradation >= warning_threshold:
            urgency = "high"
            score = 0.7
        elif any(p["degradation"] >= critical_threshold for p in predicted_degradation[:3]):
            urgency = "medium"
            score = 0.5
        else:
            urgency = "low"
            score = 0.2
        
        # Factor in driver twin degradation profile if available
        if driver_twin and "degradation_profile" in driver_twin:
            profile = driver_twin["degradation_profile"]
            if profile.get("rate", 0) > degradation_rate:
                score = min(1.0, score + 0.1)  # Higher degradation rate increases score
        
        return {
            "factor": "degradation",
            "weight": 0.35,  # 35% weight in decision
            "score": float(score),
            "urgency": urgency,
            "current_degradation": float(current_degradation),
            "degradation_rate": float(degradation_rate),
            "tire_age": tire_age,
            "predicted_degradation": predicted_degradation,
            "critical_lap": self._find_critical_lap(predicted_degradation, critical_threshold),
            "explanation": f"Tire degradation at {current_degradation:.1%} ({urgency} urgency). "
                          f"Predicted to reach critical threshold at lap {self._find_critical_lap(predicted_degradation, critical_threshold) or 'N/A'}"
        }
    
    def _analyze_traffic_factor(
        self,
        current_position: int,
        traffic_density: float,
        current_lap: int,
        total_laps: int,
        driver_id: str
    ) -> Dict:
        """Analyze traffic conditions factor."""
        # Calculate traffic impact
        cars_ahead = max(0, current_position - 1)
        
        # Traffic density analysis
        if traffic_density >= 0.7:
            traffic_level = "heavy"
            clear_window = False
            score = 0.3  # Heavy traffic = lower score (bad for pitting)
        elif traffic_density >= 0.4:
            traffic_level = "moderate"
            clear_window = False
            score = 0.5
        else:
            traffic_level = "light"
            clear_window = True
            score = 0.8  # Light traffic = higher score (good for pitting)
        
        # Predict traffic window for next 5 laps
        traffic_window = []
        for lap_offset in range(1, 6):
            # Traffic typically decreases as race progresses
            progress = (current_lap + lap_offset) / total_laps
            predicted_density = traffic_density * (1.0 - progress * 0.2)  # 20% reduction over race
            traffic_window.append({
                "lap": current_lap + lap_offset,
                "predicted_density": float(max(0.0, min(1.0, predicted_density))),
                "clear": predicted_density < 0.4
            })
        
        # Find best traffic window
        best_window = min(traffic_window, key=lambda w: w["predicted_density"])
        
        # Build explanation without nested f-strings (avoid backslashes in f-string expressions)
        if clear_window:
            explanation = f"Traffic density: {traffic_density:.1%} ({traffic_level}). Clear window available now"
        else:
            explanation = f"Traffic density: {traffic_density:.1%} ({traffic_level}). Best window predicted at lap {best_window['lap']}"

        return {
            "factor": "traffic",
            "weight": 0.25,  # 25% weight
            "score": float(score),
            "traffic_level": traffic_level,
            "traffic_density": float(traffic_density),
            "cars_ahead": cars_ahead,
            "clear_window_now": clear_window,
            "traffic_window": traffic_window,
            "best_window_lap": best_window["lap"] if best_window["clear"] else None,
            "explanation": explanation
        }
    
    def _analyze_race_twin_factor(
        self,
        race_twin: Optional[Dict],
        driver_id: str,
        current_lap: int,
        total_laps: int
    ) -> Dict:
        """Analyze Race Twin simulation factor."""
        if not race_twin:
            return {
                "factor": "race_twin",
                "weight": 0.20,
                "score": 0.5,  # Neutral if no data
                "available": False,
                "explanation": "Race Twin data not available - using neutral score"
            }
        
        # Extract Race Twin insights
        insights = {}
        score = 0.5  # Start neutral
        
        # Check pit recommendations from Race Twin
        pit_recommendations = race_twin.get("pit_recommendations", {})
        if pit_recommendations:
            optimal_window = pit_recommendations.get("optimal_window", {})
            window_start = optimal_window.get("start", current_lap)
            window_end = optimal_window.get("end", current_lap + 10)
            
            # Check if current lap is in optimal window
            if window_start <= current_lap <= window_end:
                score = 0.8  # In optimal window
                insights["optimal_window"] = True
                insights["window"] = f"Laps {window_start}-{window_end}"
            elif current_lap < window_start:
                laps_to_window = window_start - current_lap
                score = 0.4  # Before optimal window
                insights["optimal_window"] = False
                insights["laps_to_window"] = laps_to_window
            else:
                score = 0.3  # Past optimal window
                insights["optimal_window"] = False
                insights["past_window"] = True
        
        # Check undercut opportunities
        undercut_outcomes = race_twin.get("undercut_outcomes", {})
        if undercut_outcomes.get("viable", False):
            time_gain = undercut_outcomes.get("time_gain", 0.0)
            if time_gain > 2.0:
                score = 0.9  # Strong undercut opportunity
                insights["undercut_viable"] = True
                insights["undercut_gain"] = time_gain
            elif time_gain > 1.0:
                score = 0.7  # Moderate undercut
                insights["undercut_viable"] = True
                insights["undercut_gain"] = time_gain
        
        # Check tire cliff prediction
        tire_cliff = race_twin.get("tire_cliff_prediction", {})
        if tire_cliff.get("critical", False):
            cliff_lap = tire_cliff.get("lap", current_lap + 20)
            laps_to_cliff = cliff_lap - current_lap
            if laps_to_cliff <= 3:
                score = max(score, 0.9)  # Very close to cliff
                insights["tire_cliff_imminent"] = True
                insights["cliff_lap"] = cliff_lap
        
        # Check traffic simulation
        traffic_sim = race_twin.get("traffic_simulation", {})
        if traffic_sim.get("clear_window", False):
            score = min(1.0, score + 0.1)  # Clear window increases score
            insights["clear_window"] = True
        
        return {
            "factor": "race_twin",
            "weight": 0.20,  # 20% weight
            "score": float(score),
            "available": True,
            "insights": insights,
            "explanation": f"Race Twin analysis: {insights.get('optimal_window', 'N/A')}, "
                          f"Undercut: {undercut_outcomes.get('viable', False)}, "
                          f"Tire cliff: {tire_cliff.get('critical', False)}"
        }
    
    def _analyze_opponent_factor(
        self,
        opponent_data: Optional[List[Dict]],
        current_lap: int,
        tire_age: int,
        driver_id: str
    ) -> Dict:
        """Analyze opponent strategy factor."""
        if not opponent_data or len(opponent_data) == 0:
            return {
                "factor": "opponent",
                "weight": 0.10,
                "score": 0.5,
                "available": False,
                "explanation": "Opponent data not available"
            }
        
        # Find closest opponent
        closest_opponent = None
        min_gap = float('inf')
        
        for opponent in opponent_data:
            gap = abs(opponent.get("gap", 0))
            if gap < min_gap:
                min_gap = gap
                closest_opponent = opponent
        
        if not closest_opponent:
            return {
                "factor": "opponent",
                "weight": 0.10,
                "score": 0.5,
                "available": False,
                "explanation": "No opponent data available"
            }
        
        # Analyze opponent tire age vs our tire age
        opponent_tire_age = closest_opponent.get("tire_age", tire_age)
        tire_age_delta = tire_age - opponent_tire_age
        
        score = 0.5  # Neutral
        
        # If opponent has much older tires, we can extend
        if tire_age_delta < -5:
            score = 0.3  # Opponent will pit soon, we can wait
        # If we have much older tires, we should pit
        elif tire_age_delta > 5:
            score = 0.8  # We need to pit before opponent
        
        # Check if opponent just pitted (undercut opportunity)
        if closest_opponent.get("just_pitted", False):
            score = 0.7  # Opponent just pitted, we can undercut
        
        return {
            "factor": "opponent",
            "weight": 0.10,  # 10% weight
            "score": float(score),
            "available": True,
            "opponent_tire_age": opponent_tire_age,
            "tire_age_delta": tire_age_delta,
            "closest_opponent": closest_opponent.get("id", "unknown"),
            "explanation": f"Opponent tire age: {opponent_tire_age} laps (delta: {tire_age_delta:+d}). "
                          f"{'We can extend' if tire_age_delta < -5 else 'We should pit soon' if tire_age_delta > 5 else 'Similar tire age'}"
        }
    
    def _analyze_weather_factor(
        self,
        weather_data: Optional[Dict],
        tire_compound: str
    ) -> Dict:
        """Analyze weather conditions factor."""
        if not weather_data:
            return {
                "factor": "weather",
                "weight": 0.10,
                "score": 0.5,
                "available": False,
                "explanation": "Weather data not available"
            }
        
        score = 0.5  # Neutral
        
        # Check for rain
        condition = weather_data.get("condition", "dry").lower()
        if "rain" in condition or "wet" in condition:
            # In wet conditions, pit timing is less critical
            score = 0.4
        elif condition == "dry":
            # Dry conditions = normal pit strategy
            score = 0.5
        
        # Temperature effects
        track_temp = weather_data.get("track_temp", 25.0)
        if track_temp > 35:
            # Hot track = faster degradation
            score = min(1.0, score + 0.2)
        elif track_temp < 15:
            # Cold track = slower degradation
            score = max(0.0, score - 0.1)
        
        return {
            "factor": "weather",
            "weight": 0.10,  # 10% weight
            "score": float(score),
            "available": True,
            "condition": condition,
            "track_temp": track_temp,
            "explanation": f"Weather: {condition}, Track temp: {track_temp}°C"
        }
    
    def _calculate_confidence_score(
        self,
        degradation_factor: Dict,
        traffic_factor: Dict,
        race_twin_factor: Dict,
        opponent_factor: Dict,
        weather_factor: Dict
    ) -> float:
        """Calculate overall confidence score (0-1)."""
        # Weighted average of all factors
        total_score = (
            degradation_factor["score"] * degradation_factor["weight"] +
            traffic_factor["score"] * traffic_factor["weight"] +
            race_twin_factor["score"] * race_twin_factor["weight"] +
            opponent_factor["score"] * opponent_factor["weight"] +
            weather_factor["score"] * weather_factor["weight"]
        )
        
        # Adjust confidence based on data availability
        available_factors = sum([
            degradation_factor.get("available", True),
            traffic_factor.get("available", True),
            race_twin_factor.get("available", False),
            opponent_factor.get("available", False),
            weather_factor.get("available", False)
        ])
        
        # More available factors = higher confidence
        availability_multiplier = 0.7 + (available_factors / 5.0) * 0.3
        
        confidence = total_score * availability_multiplier
        
        return float(max(0.0, min(1.0, confidence)))
    
    def _make_decision(
        self,
        degradation_factor: Dict,
        traffic_factor: Dict,
        race_twin_factor: Dict,
        opponent_factor: Dict,
        weather_factor: Dict,
        confidence_score: float,
        current_lap: int,
        total_laps: int,
        tire_age: int
    ) -> Dict:
        """Make final pit decision based on all factors."""
        # Decision thresholds
        pit_now_threshold = 0.75
        pit_later_threshold = 0.55
        
        # Check for critical conditions
        if degradation_factor["urgency"] == "critical":
            decision = "PIT_NOW"
            recommended_lap = current_lap
            reasoning = [
                f"Critical tire degradation detected ({degradation_factor['current_degradation']:.1%})",
                f"Tire age: {tire_age} laps - exceeds safe threshold"
            ]
        elif confidence_score >= pit_now_threshold:
            decision = "PIT_NOW"
            recommended_lap = current_lap
            reasoning = [
                f"High confidence score ({confidence_score:.2f}) indicates optimal pit window",
                f"Traffic conditions: {traffic_factor['traffic_level']}",
                f"Degradation urgency: {degradation_factor['urgency']}"
            ]
        elif confidence_score >= pit_later_threshold:
            # Find best lap in next few laps
            best_traffic_lap = traffic_factor.get("best_window_lap")
            if best_traffic_lap and best_traffic_lap <= current_lap + 5:
                decision = "PIT_LATER"
                recommended_lap = best_traffic_lap
            else:
                decision = "PIT_LATER"
                recommended_lap = current_lap + 2  # Default: 2 laps from now
            reasoning = [
                f"Moderate confidence ({confidence_score:.2f}) - pit window opening soon",
                f"Recommended lap: {recommended_lap}",
                f"Traffic window: {traffic_factor.get('best_window_lap', 'N/A')}"
            ]
        else:
            decision = "EXTEND_STINT"
            recommended_lap = None
            reasoning = [
                f"Low confidence ({confidence_score:.2f}) - extend current stint",
                f"Tires still viable (age: {tire_age} laps)",
                f"Better pit window expected later"
            ]
        
        # Add Race Twin insights to reasoning
        if race_twin_factor.get("available") and race_twin_factor.get("insights"):
            insights = race_twin_factor["insights"]
            if insights.get("undercut_viable"):
                reasoning.append(f"Undercut opportunity: {insights.get('undercut_gain', 0):.1f}s potential gain")
            if insights.get("tire_cliff_imminent"):
                reasoning.append(f"Tire cliff imminent at lap {insights.get('cliff_lap', 'N/A')}")
        
        return {
            "decision": decision,
            "recommended_lap": recommended_lap,
            "reasoning": reasoning
        }
    
    def _generate_factor_breakdown(
        self,
        degradation_factor: Dict,
        traffic_factor: Dict,
        race_twin_factor: Dict,
        opponent_factor: Dict,
        weather_factor: Dict,
        confidence_score: float
    ) -> Dict:
        """Generate detailed factor breakdown JSON."""
        return {
            "degradation": {
                "score": degradation_factor["score"],
                "weight": degradation_factor["weight"],
                "weighted_contribution": degradation_factor["score"] * degradation_factor["weight"],
                "urgency": degradation_factor["urgency"],
                "current_degradation": degradation_factor["current_degradation"],
                "explanation": degradation_factor["explanation"]
            },
            "traffic": {
                "score": traffic_factor["score"],
                "weight": traffic_factor["weight"],
                "weighted_contribution": traffic_factor["score"] * traffic_factor["weight"],
                "traffic_level": traffic_factor["traffic_level"],
                "clear_window": traffic_factor["clear_window_now"],
                "best_window_lap": traffic_factor.get("best_window_lap"),
                "explanation": traffic_factor["explanation"]
            },
            "race_twin": {
                "score": race_twin_factor["score"],
                "weight": race_twin_factor["weight"],
                "weighted_contribution": race_twin_factor["score"] * race_twin_factor["weight"],
                "available": race_twin_factor.get("available", False),
                "insights": race_twin_factor.get("insights", {}),
                "explanation": race_twin_factor["explanation"]
            },
            "opponent": {
                "score": opponent_factor["score"],
                "weight": opponent_factor["weight"],
                "weighted_contribution": opponent_factor["score"] * opponent_factor["weight"],
                "available": opponent_factor.get("available", False),
                "explanation": opponent_factor["explanation"]
            },
            "weather": {
                "score": weather_factor["score"],
                "weight": weather_factor["weight"],
                "weighted_contribution": weather_factor["score"] * weather_factor["weight"],
                "available": weather_factor.get("available", False),
                "explanation": weather_factor["explanation"]
            },
            "overall_confidence": confidence_score,
            "confidence_level": self._confidence_level(confidence_score)
        }
    
    def _find_critical_lap(self, predicted_degradation: List[Dict], threshold: float) -> Optional[int]:
        """Find the lap where degradation reaches critical threshold."""
        for pred in predicted_degradation:
            if pred["degradation"] >= threshold:
                return pred["lap"]
        return None
    
    def _confidence_level(self, score: float) -> str:
        """Convert confidence score to level."""
        if score >= 0.8:
            return "high"
        elif score >= 0.6:
            return "medium-high"
        elif score >= 0.4:
            return "medium"
        elif score >= 0.2:
            return "low-medium"
        else:
            return "low"


def make_advanced_pit_decision(
    driver_id: str,
    current_lap: int,
    total_laps: int,
    tire_age: int,
    tire_compound: str,
    current_position: int,
    degradation_rate: float,
    traffic_density: float,
    **kwargs
) -> Dict:
    """
    Convenience function for advanced pit decision.
    """
    engine = AdvancedPitDecisionEngine()
    return engine.make_pit_decision(
        driver_id=driver_id,
        current_lap=current_lap,
        total_laps=total_laps,
        tire_age=tire_age,
        tire_compound=tire_compound,
        current_position=current_position,
        degradation_rate=degradation_rate,
        traffic_density=traffic_density,
        **kwargs
    )

