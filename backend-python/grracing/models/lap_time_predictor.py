"""
Production Lap Time Prediction Model

Full ML model for predicting future lap times based on multiple factors.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import joblib
import os
from pathlib import Path

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class LapTimePredictor:
    """
    Production lap time prediction model.
    
    Features:
    - Temperature (track and ambient)
    - Tire age (laps on tires)
    - Stint number
    - Fuel load
    - Track condition
    - Sector times
    - Driver metrics
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        # Use absolute path from backend-python directory
        if model_path:
            self.model_path = model_path
        else:
            # Default to models directory in backend-python
            # __file__ is grracing/models/lap_time_predictor.py
            # Go up: grracing/models -> grracing -> backend-python
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            models_dir = os.path.join(base_dir, "models")
            os.makedirs(models_dir, exist_ok=True)  # Ensure directory exists
            self.model_path = os.path.join(models_dir, "lap_time_predictor.joblib")
        self.is_trained = False
        
        # Load existing model if available
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                self.is_trained = True
                print(f"✅ Loaded trained model from {self.model_path}")
            except Exception as e:
                print(f"⚠️ Could not load model: {e}")
        
        # Initialize default model if none loaded
        if not self.model:
            self._initialize_default_model()
    
    def _initialize_default_model(self):
        """Initialize a default model (trained or untrained)."""
        if XGBOOST_AVAILABLE:
            self.model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
        elif SKLEARN_AVAILABLE:
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
        else:
            # Fallback to simple linear model
            print("⚠️ XGBoost and scikit-learn not available, using simple model")
            self.model = SimpleLapTimeModel()
    
    def train(
        self,
        features: np.ndarray,
        target: np.ndarray,
        test_size: float = 0.2,
        save_model: bool = True
    ) -> Dict:
        """
        Train the lap time prediction model.
        
        Args:
            features: Feature matrix (n_samples, n_features)
            target: Target lap times (n_samples,)
            test_size: Fraction of data for testing
            save_model: Whether to save trained model
            
        Returns:
            Training metrics (RMSE, R²)
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
        print("Training lap time prediction model...")
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
    
    def predict(
        self,
        track_temp: float,
        ambient_temp: float,
        tire_age: int,
        stint_number: int,
        fuel_load: float,
        track_condition: str = "dry",
        sector_times: Optional[Dict[str, float]] = None,
        driver_pace_vector: float = 0.0,
        driver_consistency: float = 0.8,
        base_lap_time: float = 95.0
    ) -> Dict:
        """
        Predict lap time given features.
        
        Args:
            track_temp: Track temperature in Celsius
            ambient_temp: Ambient temperature in Celsius
            tire_age: Number of laps on current tires
            stint_number: Current stint number (1, 2, 3...)
            fuel_load: Fuel load percentage (0-100)
            track_condition: "dry", "wet", "damp", "mixed"
            sector_times: Optional sector times (S1, S2, S3)
            driver_pace_vector: Driver pace vector from twin
            driver_consistency: Driver consistency index
            base_lap_time: Base lap time for track
            
        Returns:
            Predicted lap time and confidence
        """
        # Prepare features
        features = self._prepare_features(
            track_temp=track_temp,
            ambient_temp=ambient_temp,
            tire_age=tire_age,
            stint_number=stint_number,
            fuel_load=fuel_load,
            track_condition=track_condition,
            sector_times=sector_times,
            driver_pace_vector=driver_pace_vector,
            driver_consistency=driver_consistency,
            base_lap_time=base_lap_time
        )
        
        # Predict
        if self.is_trained and hasattr(self.model, 'predict'):
            try:
                prediction = self.model.predict(features.reshape(1, -1))[0]
                confidence = 0.9
            except Exception as e:
                print(f"⚠️ Model prediction failed: {e}, using fallback")
                prediction = self._fallback_prediction(features, base_lap_time)
                confidence = 0.5
        else:
            prediction = self._fallback_prediction(features, base_lap_time)
            confidence = 0.7
        
        return {
            "predicted_lap_time": float(prediction),
            "confidence": float(confidence),
            "base_lap_time": float(base_lap_time),
            "factors": {
                "temperature_effect": float((track_temp - 25) * 0.002),  # 0.2% per degree
                "tire_degradation": float(tire_age * 0.002),  # 0.2% per lap
                "fuel_effect": float((100 - fuel_load) * 0.0001),  # Lighter = faster
                "pace_vector_effect": float(driver_pace_vector * base_lap_time)
            }
        }
    
    def _prepare_features(
        self,
        track_temp: float,
        ambient_temp: float,
        tire_age: int,
        stint_number: int,
        fuel_load: float,
        track_condition: str,
        sector_times: Optional[Dict],
        driver_pace_vector: float,
        driver_consistency: float,
        base_lap_time: float
    ) -> np.ndarray:
        """
        Prepare feature vector for model.
        """
        # Track condition encoding
        condition_map = {"dry": 0, "damp": 1, "wet": 2, "mixed": 3}
        condition_encoded = condition_map.get(track_condition, 0)
        
        # Sector times (if available)
        s1_time = sector_times.get("S1", 0) if sector_times else 0
        s2_time = sector_times.get("S2", 0) if sector_times else 0
        s3_time = sector_times.get("S3", 0) if sector_times else 0
        
        # Feature vector
        features = np.array([
            track_temp,
            ambient_temp,
            tire_age,
            stint_number,
            fuel_load / 100.0,  # Normalize to 0-1
            condition_encoded,
            s1_time,
            s2_time,
            s3_time,
            driver_pace_vector,
            driver_consistency,
            base_lap_time
        ])
        
        return features
    
    def _fallback_prediction(
        self,
        features: np.ndarray,
        base_lap_time: float
    ) -> float:
        """
        Fallback prediction using simple formula if model not trained.
        """
        track_temp, ambient_temp, tire_age, stint, fuel_load, condition, s1, s2, s3, pace_vec, consistency, base = features
        
        # Simple formula-based prediction
        predicted = base_lap_time
        
        # Temperature effect (optimal around 25°C)
        temp_effect = (track_temp - 25) * 0.002
        predicted *= (1.0 + temp_effect)
        
        # Tire degradation
        degradation = tire_age * 0.002
        predicted *= (1.0 + degradation)
        
        # Fuel effect (lighter = faster)
        fuel_effect = (100 - fuel_load * 100) * 0.0001
        predicted *= (1.0 - fuel_effect)
        
        # Track condition
        condition_multipliers = {0: 1.0, 1: 1.08, 2: 1.15, 3: 1.12}
        predicted *= condition_multipliers.get(int(condition), 1.0)
        
        # Driver pace vector
        predicted *= (1.0 + pace_vec)
        
        # Consistency variance (less consistent = more variance)
        variance = (1.0 - consistency) * 0.5
        predicted += np.random.normal(0, variance)
        
        return max(predicted, 90.0)  # Minimum cap


class SimpleLapTimeModel:
    """Simple fallback model if ML libraries not available."""
    
    def fit(self, X, y):
        pass
    
    def predict(self, X):
        # Simple average-based prediction
        if len(X.shape) == 2:
            # Use last feature (base_lap_time) as prediction
            return X[:, -1]
        else:
            return X[-1]


if __name__ == "__main__":
    # Test lap time predictor
    predictor = LapTimePredictor()
    
    # Make prediction
    result = predictor.predict(
        track_temp=28.0,
        ambient_temp=25.0,
        tire_age=15,
        stint_number=1,
        fuel_load=0.8,
        track_condition="dry",
        sector_times={"S1": 31.5, "S2": 32.0, "S3": 31.7},
        driver_pace_vector=0.05,
        driver_consistency=0.9,
        base_lap_time=95.0
    )
    
    print(f"Predicted lap time: {result['predicted_lap_time']:.3f}s")
    print(f"Confidence: {result['confidence']:.2f}")

