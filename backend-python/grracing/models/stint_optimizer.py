"""
Stint Length Optimizer - ML Model

Optimizes stint length based on:
- Tire degradation curves
- Fuel consumption
- Traffic patterns
- Weather conditions
- Driver fatigue
- Pit window opportunities
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import joblib
import os
from pathlib import Path

try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False


class StintLengthOptimizer:
    """
    ML model to optimize stint length for race strategy.
    
    Predicts optimal stint length considering:
    - Tire degradation rate
    - Fuel consumption
    - Traffic patterns
    - Weather conditions
    - Driver performance
    - Pit window opportunities
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        if model_path:
            self.model_path = model_path
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            models_dir = os.path.join(base_dir, "models")
            os.makedirs(models_dir, exist_ok=True)
            self.model_path = os.path.join(models_dir, "stint_optimizer.joblib")
        self.is_trained = False
        
        # Load existing model if available
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                self.is_trained = True
                print(f"✅ Loaded trained stint optimizer from {self.model_path}")
            except Exception as e:
                print(f"⚠️ Could not load model: {e}")
        
        # Initialize default model if none loaded
        if not self.model:
            self._initialize_default_model()
    
    def _initialize_default_model(self):
        """Initialize a default model."""
        if XGBOOST_AVAILABLE:
            self.model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        elif SKLEARN_AVAILABLE:
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        else:
            self.model = SimpleStintOptimizer()
    
    def train(
        self,
        features: np.ndarray,
        target: np.ndarray,
        test_size: float = 0.2,
        save_model: bool = True
    ) -> Dict:
        """
        Train the stint length optimizer model.
        
        Args:
            features: Feature matrix (n_samples, n_features)
            target: Target optimal stint lengths (n_samples,)
            test_size: Fraction of data for testing
            save_model: Whether to save trained model
            
        Returns:
            Training metrics
        """
        if not SKLEARN_AVAILABLE and not XGBOOST_AVAILABLE:
            return {
                "status": "error",
                "message": "ML libraries not available"
            }
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            features, target, test_size=test_size, random_state=42
        )
        
        # Train model
        print("Training stint length optimizer...")
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # Evaluate
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)
        
        train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
        train_r2 = r2_score(y_train, y_pred_train)
        test_r2 = r2_score(y_test, y_pred_test)
        
        metrics = {
            "status": "success",
            "train_rmse": float(train_rmse),
            "test_rmse": float(test_rmse),
            "train_r2": float(train_r2),
            "test_r2": float(test_r2)
        }
        
        # Save model
        if save_model:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump(self.model, self.model_path)
            print(f"✅ Model saved to {self.model_path}")
        
        return metrics
    
    def optimize_stint_length(
        self,
        degradation_rate: float,
        tire_compound: str,
        fuel_consumption_per_lap: float,
        total_fuel_capacity: float,
        traffic_density: float,
        track_temp: float,
        driver_fatigue_factor: float,
        current_lap: int,
        total_laps: int,
        pit_window_start: int = 15,
        pit_window_end: int = 25
    ) -> Dict:
        """
        Optimize stint length based on multiple factors.
        
        Args:
            degradation_rate: Tire degradation rate per lap
            tire_compound: Tire compound (SOFT, MEDIUM, HARD)
            fuel_consumption_per_lap: Fuel consumed per lap (kg)
            total_fuel_capacity: Total fuel capacity (kg)
            traffic_density: Current traffic density (0-1)
            track_temp: Track temperature (Celsius)
            driver_fatigue_factor: Driver fatigue factor (0-1)
            current_lap: Current lap number
            total_laps: Total race laps
            pit_window_start: Start of pit window
            pit_window_end: End of pit window
            
        Returns:
            Optimal stint length and reasoning
        """
        # Prepare features
        features = self._prepare_features(
            degradation_rate=degradation_rate,
            tire_compound=tire_compound,
            fuel_consumption_per_lap=fuel_consumption_per_lap,
            total_fuel_capacity=total_fuel_capacity,
            traffic_density=traffic_density,
            track_temp=track_temp,
            driver_fatigue_factor=driver_fatigue_factor,
            current_lap=current_lap,
            total_laps=total_laps,
            pit_window_start=pit_window_start,
            pit_window_end=pit_window_end
        )
        
        # Predict optimal stint length
        if self.is_trained and hasattr(self.model, 'predict'):
            try:
                predicted_stint = self.model.predict(features.reshape(1, -1))[0]
                confidence = 0.9
            except Exception as e:
                print(f"⚠️ Model prediction failed: {e}, using fallback")
                predicted_stint = self._fallback_optimization(features)
                confidence = 0.5
        else:
            predicted_stint = self._fallback_optimization(features)
            confidence = 0.7
        
        # Clamp to reasonable range
        optimal_stint = max(5, min(int(predicted_stint), total_laps - current_lap))
        
        # Calculate reasoning
        reasoning = self._generate_reasoning(
            optimal_stint=optimal_stint,
            degradation_rate=degradation_rate,
            tire_compound=tire_compound,
            fuel_consumption_per_lap=fuel_consumption_per_lap,
            total_fuel_capacity=total_fuel_capacity,
            traffic_density=traffic_density,
            current_lap=current_lap,
            pit_window_start=pit_window_start,
            pit_window_end=pit_window_end
        )
        
        return {
            "optimal_stint_length": optimal_stint,
            "recommended_pit_lap": current_lap + optimal_stint,
            "confidence": float(confidence),
            "reasoning": reasoning,
            "factors": {
                "degradation_limited": degradation_rate > 0.003,
                "fuel_limited": (total_fuel_capacity / fuel_consumption_per_lap) < optimal_stint,
                "traffic_optimal": traffic_density < 0.4,
                "within_pit_window": (current_lap + optimal_stint) >= pit_window_start and (current_lap + optimal_stint) <= pit_window_end
            }
        }
    
    def _prepare_features(
        self,
        degradation_rate: float,
        tire_compound: str,
        fuel_consumption_per_lap: float,
        total_fuel_capacity: float,
        traffic_density: float,
        track_temp: float,
        driver_fatigue_factor: float,
        current_lap: int,
        total_laps: int,
        pit_window_start: int,
        pit_window_end: int
    ) -> np.ndarray:
        """Prepare feature vector for model."""
        # Compound encoding
        compound_map = {"SOFT": 0, "MEDIUM": 1, "HARD": 2, "SUPER_SOFT": 0, "INTERMEDIATE": 3, "WET": 4}
        compound_encoded = compound_map.get(tire_compound, 1)
        
        # Fuel-limited stint length
        fuel_limited_stint = total_fuel_capacity / fuel_consumption_per_lap if fuel_consumption_per_lap > 0 else 30
        
        # Degradation-limited stint length (when degradation becomes critical)
        degradation_limited_stint = 20 / degradation_rate if degradation_rate > 0 else 30
        
        # Pit window center
        pit_window_center = (pit_window_start + pit_window_end) / 2
        
        # Laps remaining
        laps_remaining = total_laps - current_lap
        
        # Feature vector
        features = np.array([
            degradation_rate,
            compound_encoded,
            fuel_consumption_per_lap,
            total_fuel_capacity,
            traffic_density,
            track_temp,
            driver_fatigue_factor,
            current_lap,
            total_laps,
            pit_window_start,
            pit_window_end,
            pit_window_center,
            laps_remaining,
            fuel_limited_stint,
            degradation_limited_stint
        ])
        
        return features
    
    def _fallback_optimization(self, features: np.ndarray) -> float:
        """
        Fallback optimization using rule-based approach.
        """
        degradation_rate, compound, fuel_cons, fuel_cap, traffic, temp, fatigue, current, total, pit_start, pit_end, pit_center, laps_rem, fuel_lim, deg_lim = features
        
        # Start with degradation-limited stint
        optimal = min(fuel_lim, deg_lim)
        
        # Adjust for traffic (lower traffic = can extend)
        if traffic < 0.4:
            optimal *= 1.1  # Extend 10% if low traffic
        elif traffic > 0.7:
            optimal *= 0.9  # Shorten 10% if high traffic
        
        # Adjust for pit window (prefer pitting in window)
        target_pit_lap = current + optimal
        if target_pit_lap < pit_start:
            optimal = pit_start - current  # Extend to reach window
        elif target_pit_lap > pit_end:
            optimal = pit_end - current  # Shorten to fit in window
        
        # Clamp to reasonable range
        optimal = max(5, min(optimal, laps_rem, 30))
        
        return optimal
    
    def _generate_reasoning(
        self,
        optimal_stint: int,
        degradation_rate: float,
        tire_compound: str,
        fuel_consumption_per_lap: float,
        total_fuel_capacity: float,
        traffic_density: float,
        current_lap: int,
        pit_window_start: int,
        pit_window_end: int
    ) -> List[str]:
        """Generate human-readable reasoning for stint length."""
        reasoning = []
        
        # Degradation reasoning
        if degradation_rate > 0.003:
            reasoning.append(f"High degradation rate ({degradation_rate:.4f}) limits stint to {optimal_stint} laps")
        else:
            reasoning.append(f"Moderate degradation allows {optimal_stint} lap stint")
        
        # Fuel reasoning
        fuel_limited = (total_fuel_capacity / fuel_consumption_per_lap) < optimal_stint
        if fuel_limited:
            reasoning.append(f"Fuel capacity limits stint to {int(total_fuel_capacity / fuel_consumption_per_lap)} laps")
        
        # Traffic reasoning
        if traffic_density < 0.4:
            reasoning.append("Low traffic density - good conditions to extend stint")
        elif traffic_density > 0.7:
            reasoning.append("High traffic density - consider shorter stint for better pit window")
        
        # Pit window reasoning
        recommended_pit = current_lap + optimal_stint
        if pit_window_start <= recommended_pit <= pit_window_end:
            reasoning.append(f"Recommended pit at lap {recommended_pit} falls within optimal pit window ({pit_window_start}-{pit_window_end})")
        else:
            reasoning.append(f"Adjust stint to pit within window ({pit_window_start}-{pit_window_end})")
        
        return reasoning


class SimpleStintOptimizer:
    """Simple fallback optimizer if ML libraries not available."""
    
    def fit(self, X, y):
        pass
    
    def predict(self, X):
        # Simple rule-based prediction
        if len(X.shape) == 2:
            # Use degradation and fuel limited stints
            fuel_limited = X[:, 13]  # fuel_limited_stint
            deg_limited = X[:, 14]   # degradation_limited_stint
            return np.minimum(fuel_limited, deg_limited)
        else:
            return min(X[13], X[14])


if __name__ == "__main__":
    # Test stint optimizer
    optimizer = StintLengthOptimizer()
    
    result = optimizer.optimize_stint_length(
        degradation_rate=0.0025,
        tire_compound="MEDIUM",
        fuel_consumption_per_lap=2.5,
        total_fuel_capacity=100.0,
        traffic_density=0.4,
        track_temp=28.0,
        driver_fatigue_factor=0.1,
        current_lap=10,
        total_laps=50,
        pit_window_start=18,
        pit_window_end=22
    )
    
    print("Stint Optimization Result:")
    print(result)

