"""
ML-Based Tire Degradation Model

Uses machine learning to predict tire degradation based on:
- Tire compound
- Track temperature
- Tire age
- Track surface
- Weather conditions
- Driver style
"""

import numpy as np
from typing import Dict, List, Optional
import joblib
import os

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


class MLTireDegradationModel:
    """
    ML-based tire degradation prediction model.
    
    Predicts degradation rate and pace loss using machine learning.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        if model_path:
            self.model_path = model_path
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            models_dir = os.path.join(base_dir, "models")
            os.makedirs(models_dir, exist_ok=True)
            self.model_path = os.path.join(models_dir, "ml_tire_degradation.joblib")
        self.is_trained = False
        
        # Load existing model if available
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                self.is_trained = True
                print(f"✅ Loaded trained ML tire degradation model from {self.model_path}")
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
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
        elif SKLEARN_AVAILABLE:
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
        else:
            self.model = SimpleDegradationModel()
    
    def train(
        self,
        features: np.ndarray,
        target: np.ndarray,
        test_size: float = 0.2,
        save_model: bool = True
    ) -> Dict:
        """
        Train the ML tire degradation model.
        
        Args:
            features: Feature matrix (n_samples, n_features)
            target: Target degradation rates (n_samples,)
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
        print("Training ML tire degradation model...")
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
    
    def predict_degradation(
        self,
        tire_age: int,
        tire_compound: str,
        track_temp: float,
        ambient_temp: float,
        track_surface: str = "smooth",
        driver_aggression: float = 0.5,
        base_pace: float = 95.0
    ) -> Dict:
        """
        Predict tire degradation using ML model.
        
        Args:
            tire_age: Number of laps on tires
            tire_compound: Tire compound (SOFT, MEDIUM, HARD)
            track_temp: Track temperature (Celsius)
            ambient_temp: Ambient temperature (Celsius)
            track_surface: Track surface type
            driver_aggression: Driver aggression score (0-1)
            base_pace: Base lap time
            
        Returns:
            Degradation prediction
        """
        # Prepare features
        features = self._prepare_features(
            tire_age=tire_age,
            tire_compound=tire_compound,
            track_temp=track_temp,
            ambient_temp=ambient_temp,
            track_surface=track_surface,
            driver_aggression=driver_aggression,
            base_pace=base_pace
        )
        
        # Predict degradation rate
        if self.is_trained and hasattr(self.model, 'predict'):
            try:
                degradation_rate = self.model.predict(features.reshape(1, -1))[0]
                confidence = 0.9
            except Exception as e:
                print(f"⚠️ Model prediction failed: {e}, using fallback")
                degradation_rate = self._fallback_degradation(features)
                confidence = 0.5
        else:
            degradation_rate = self._fallback_degradation(features)
            confidence = 0.7
        
        # Calculate pace loss
        pace_loss = base_pace * degradation_rate * tire_age
        
        # Detect tire cliff
        is_cliff = degradation_rate > 0.003 and tire_age > 20
        
        return {
            "tire_age": tire_age,
            "degradation_rate": float(degradation_rate),
            "pace_loss": float(pace_loss),
            "predicted_pace": float(base_pace + pace_loss),
            "is_cliff": is_cliff,
            "cliff_lap": int(20 / degradation_rate) if degradation_rate > 0 else 30,
            "confidence": float(confidence),
            "compound": tire_compound
        }
    
    def _prepare_features(
        self,
        tire_age: int,
        tire_compound: str,
        track_temp: float,
        ambient_temp: float,
        track_surface: str,
        driver_aggression: float,
        base_pace: float
    ) -> np.ndarray:
        """Prepare feature vector."""
        # Compound encoding
        compound_map = {"SOFT": 0, "MEDIUM": 1, "HARD": 2, "SUPER_SOFT": 0, "INTERMEDIATE": 3, "WET": 4}
        compound_encoded = compound_map.get(tire_compound, 1)
        
        # Surface encoding
        surface_map = {"smooth": 0, "rough": 1, "abrasive": 2, "mixed": 3}
        surface_encoded = surface_map.get(track_surface, 0)
        
        # Temperature delta
        temp_delta = track_temp - ambient_temp
        
        # Feature vector
        features = np.array([
            tire_age,
            compound_encoded,
            track_temp,
            ambient_temp,
            temp_delta,
            surface_encoded,
            driver_aggression,
            base_pace
        ])
        
        return features
    
    def _fallback_degradation(self, features: np.ndarray) -> float:
        """Fallback degradation calculation."""
        tire_age, compound, track_temp, ambient_temp, temp_delta, surface, aggression, base_pace = features
        
        # Base degradation rate by compound
        compound_rates = {0: 0.003, 1: 0.002, 2: 0.0015, 3: 0.004, 4: 0.005}
        base_rate = compound_rates.get(int(compound), 0.002)
        
        # Temperature effect
        temp_effect = 1.0 + ((track_temp - 25) * 0.01)
        
        # Aggression effect (more aggressive = more degradation)
        aggression_effect = 1.0 + (aggression * 0.2)
        
        # Surface effect
        surface_effects = {0: 1.0, 1: 1.1, 2: 1.2, 3: 1.05}
        surface_effect = surface_effects.get(int(surface), 1.0)
        
        # Combined degradation rate
        degradation_rate = base_rate * temp_effect * aggression_effect * surface_effect
        
        return min(degradation_rate, 0.01)  # Cap at 1% per lap


class SimpleDegradationModel:
    """Simple fallback model."""
    
    def fit(self, X, y):
        pass
    
    def predict(self, X):
        # Simple rule-based prediction
        if len(X.shape) == 2:
            tire_age = X[:, 0]
            compound = X[:, 1]
            track_temp = X[:, 2]
            
            compound_rates = {0: 0.003, 1: 0.002, 2: 0.0015}
            base_rates = np.array([compound_rates.get(int(c), 0.002) for c in compound])
            temp_effects = 1.0 + ((track_temp - 25) * 0.01)
            
            return base_rates * temp_effects
        else:
            compound_rates = {0: 0.003, 1: 0.002, 2: 0.0015}
            base_rate = compound_rates.get(int(X[1]), 0.002)
            temp_effect = 1.0 + ((X[2] - 25) * 0.01)
            return base_rate * temp_effect


if __name__ == "__main__":
    # Test ML degradation model
    model = MLTireDegradationModel()
    
    result = model.predict_degradation(
        tire_age=15,
        tire_compound="MEDIUM",
        track_temp=28.0,
        ambient_temp=25.0,
        track_surface="smooth",
        driver_aggression=0.6,
        base_pace=95.0
    )
    
    print("ML Degradation Prediction:")
    print(result)

