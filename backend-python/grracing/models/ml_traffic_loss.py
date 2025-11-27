"""
ML-Based Traffic Loss Model

Uses machine learning to predict time lost due to traffic.
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


class MLTrafficLossModel:
    """
    ML-based traffic loss prediction model.
    
    Predicts time lost due to traffic using machine learning.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        if model_path:
            self.model_path = model_path
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            models_dir = os.path.join(base_dir, "models")
            os.makedirs(models_dir, exist_ok=True)
            self.model_path = os.path.join(models_dir, "ml_traffic_loss.joblib")
        self.is_trained = False
        
        # Load existing model if available
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                self.is_trained = True
                print(f"✅ Loaded trained ML traffic loss model from {self.model_path}")
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
            self.model = SimpleTrafficLossModel()
    
    def train(
        self,
        features: np.ndarray,
        target: np.ndarray,
        test_size: float = 0.2,
        save_model: bool = True
    ) -> Dict:
        """Train the ML traffic loss model."""
        if not SKLEARN_AVAILABLE and not XGBOOST_AVAILABLE:
            return {"status": "error", "message": "ML libraries not available"}
        
        X_train, X_test, y_train, y_test = train_test_split(
            features, target, test_size=test_size, random_state=42
        )
        
        print("Training ML traffic loss model...")
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
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
        
        if save_model:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump(self.model, self.model_path)
            print(f"✅ Model saved to {self.model_path}")
        
        return metrics
    
    def predict_traffic_loss(
        self,
        cars_ahead: int,
        sector: str,
        traffic_density: float,
        driver_position: int,
        total_cars: int,
        track_type: str = "road_course"
    ) -> Dict:
        """
        Predict traffic loss using ML model.
        """
        features = self._prepare_features(
            cars_ahead=cars_ahead,
            sector=sector,
            traffic_density=traffic_density,
            driver_position=driver_position,
            total_cars=total_cars,
            track_type=track_type
        )
        
        if self.is_trained and hasattr(self.model, 'predict'):
            try:
                traffic_loss = self.model.predict(features.reshape(1, -1))[0]
                confidence = 0.9
            except Exception as e:
                print(f"⚠️ Model prediction failed: {e}, using fallback")
                traffic_loss = self._fallback_traffic_loss(features)
                confidence = 0.5
        else:
            traffic_loss = self._fallback_traffic_loss(features)
            confidence = 0.7
        
        # Clean air delta (leader has advantage)
        clean_air_delta = 0.2 if cars_ahead == 0 else 0.0
        
        return {
            "cars_ahead": cars_ahead,
            "traffic_loss": float(max(0.0, traffic_loss)),
            "clean_air_delta": float(clean_air_delta),
            "sector": sector,
            "traffic_density": float(traffic_density),
            "confidence": float(confidence)
        }
    
    def _prepare_features(
        self,
        cars_ahead: int,
        sector: str,
        traffic_density: float,
        driver_position: int,
        total_cars: int,
        track_type: str
    ) -> np.ndarray:
        """Prepare feature vector."""
        sector_map = {"S1": 0, "S2": 1, "S3": 2}
        sector_encoded = sector_map.get(sector, 1)
        
        track_map = {"road_course": 0, "oval": 1, "street": 2}
        track_encoded = track_map.get(track_type, 0)
        
        position_ratio = driver_position / total_cars if total_cars > 0 else 0.5
        
        features = np.array([
            cars_ahead,
            sector_encoded,
            traffic_density,
            driver_position,
            total_cars,
            position_ratio,
            track_encoded
        ])
        
        return features
    
    def _fallback_traffic_loss(self, features: np.ndarray) -> float:
        """Fallback traffic loss calculation."""
        cars_ahead, sector, density, position, total, position_ratio, track = features
        
        base_penalty = cars_ahead * 0.1
        
        sector_multipliers = {0: 1.0, 1: 1.2, 2: 1.1}
        sector_mult = sector_multipliers.get(int(sector), 1.0)
        
        density_penalty = density * 0.3
        
        total_loss = (base_penalty * sector_mult) + density_penalty
        
        return max(0.0, total_loss)


class SimpleTrafficLossModel:
    """Simple fallback model."""
    
    def fit(self, X, y):
        pass
    
    def predict(self, X):
        if len(X.shape) == 2:
            cars_ahead = X[:, 0]
            sector = X[:, 1]
            density = X[:, 2]
            
            sector_mults = np.array([1.0 if s == 0 else 1.2 if s == 1 else 1.1 for s in sector])
            return (cars_ahead * 0.1 * sector_mults) + (density * 0.3)
        else:
            cars_ahead, sector, density = X[0], X[1], X[2]
            sector_mult = 1.0 if sector == 0 else 1.2 if sector == 1 else 1.1
            return (cars_ahead * 0.1 * sector_mult) + (density * 0.3)


if __name__ == "__main__":
    # Test ML traffic loss model
    model = MLTrafficLossModel()
    
    result = model.predict_traffic_loss(
        cars_ahead=3,
        sector="S2",
        traffic_density=0.7,
        driver_position=5,
        total_cars=20,
        track_type="road_course"
    )
    
    print("ML Traffic Loss Prediction:")
    print(result)

