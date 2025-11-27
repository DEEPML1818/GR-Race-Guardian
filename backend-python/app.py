import os
import sys
from fastapi import FastAPI, HTTPException, UploadFile, File
import shutil
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
from pydantic import BaseModel

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from grracing.data import load_telemetry
from grracing import load_model, load_model_meta, predict  # Import from package level, not models/
from grracing.sector_timing import SectorTimingEngine, analyze_sector_performance
from grracing.lap_classification import LapClassifier, classify_lap_dataframe
from grracing.driver_metrics import DriverMetrics, analyze_driver_performance
from grracing.degradation import fit_degradation_from_data, TireDegradationModel
from grracing.monte_carlo import MonteCarloRaceSimulator, simulate_race_strategy
from grracing.driver_twin import DriverTwinGenerator, generate_driver_twin_json
from grracing.race_twin import RaceTwinSimulator, simulate_race_twin
from grracing.models.lap_time_predictor import LapTimePredictor
from grracing.models.tire_degradation import TireDegradationModel as ProductionTireDegradationModel
from grracing.models.traffic_loss import TrafficLossModel
from grracing.models.ml_tire_degradation import MLTireDegradationModel
from grracing.models.ml_traffic_loss import MLTrafficLossModel
from grracing.models.stint_optimizer import StintLengthOptimizer
from grracing.pit_rejoin import PitRejoinSimulator
from grracing.driver_twin_loop import DriverTwinUpdateLoop, get_driver_twin_loop
from grracing.strategy_optimizer import StrategyOptimizer
from grracing.strategy_console import StrategyConsoleEngine
from grracing.track_map import TrackMapEngine
from grracing.pit_decision_engine import AdvancedPitDecisionEngine
from grracing.stability_layer import get_stability_layer
from grracing.logger import setup_logging, get_logger
from grracing.track_data_parser import get_track_parser
from grracing.track_coordinates import get_track_coordinates
from grracing.race_replay_builder import RaceReplayBuilder


# Setup logging
logger = setup_logging(log_level="INFO")
stability = get_stability_layer()

app = FastAPI(
    title='GR Race Guardian ML Service',
    description='Professional motorsport analytics API',
    version='1.0.0'
)

# Add error handler middleware
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler with logging."""
    stability.log_error(exc, context={
        "endpoint": str(request.url),
        "method": request.method
    })
    return {"success": False, "error": str(exc), "recovered": False}

# In-memory storage for Race Twins (in production, use Redis or database)
race_twin_cache: Dict[str, Dict] = {}

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request, call_next):
    print(f"[REQUEST] {request.method} {request.url}")
    response = await call_next(request)
    print(f"[RESPONSE] {response.status_code}")
    return response


# Request models
class PredictRequest(BaseModel):
    csv: Optional[str] = None
    model_path: Optional[str] = 'models/merged_road_model.joblib'
    features: Optional[List[str]] = None


class SectorAnalysisRequest(BaseModel):
    csv: str
    driver_id: Optional[str] = None


class DriverMetricsRequest(BaseModel):
    csv: str
    driver_id: Optional[str] = None


class MonteCarloRequest(BaseModel):
    driver_paces: Dict[str, float]
    n_laps: int = 50
    iterations: int = 1000
    pit_strategy: Optional[Dict[str, List[int]]] = None
    compounds: Optional[Dict[str, List[str]]] = None


class PacePredictionRequest(BaseModel):
    base_lap_time: float
    lap_number: int
    compound: str = "SOFT"
    fuel_load: float = 100.0
    track_temp: float = 25.0


class DriverTwinRequest(BaseModel):
    driver_id: str
    lap_times: List[float]
    sector_times: List[Dict[str, float]]
    telemetry_data: Optional[List[Dict]] = None
    tire_compound: str = "MEDIUM"
    current_lap: int = 0


class RaceTwinRequest(BaseModel):
    race_id: str
    drivers: List[Dict]
    total_laps: int
    current_lap: int = 1
    weather_data: Optional[Dict] = None
    pit_strategy_options: Optional[List[Dict]] = None
    num_simulations: int = 500


class LapTimePredictionRequest(BaseModel):
    track_temp: float
    ambient_temp: float
    tire_age: int
    stint_number: int
    fuel_load: float
    track_condition: str = "dry"
    sector_times: Optional[Dict[str, float]] = None
    driver_pace_vector: float = 0.0
    driver_consistency: float = 0.8
    base_lap_time: float = 95.0


class StintPredictionRequest(BaseModel):
    base_lap_time: float
    laps: int
    tire_compound: str = "MEDIUM"
    track_temp: float = 25.0
    fuel_load_start: float = 100.0
    driver_pace_vector: float = 0.0


class PitDecisionRequest(BaseModel):
    race_id: str
    driver_id: str
    current_lap: int
    total_laps: int = 50
    tire_age: int
    tire_compound: str
    position: int
    degradation_rate: float = 0.002
    traffic_density: float = 0.5
    degradation_curve: Optional[Dict] = None
    traffic_simulation: Optional[Dict] = None
    race_twin: Optional[Dict] = None
    driver_twin: Optional[Dict] = None
    opponent_data: Optional[List[Dict]] = None
    weather_data: Optional[Dict] = None


class PitRejoinRequest(BaseModel):
    driver_id: str
    current_position: int
    pit_lap: int
    pit_time: float = 22.0
    average_lap_time: float = 95.0
    traffic_density: float = 0.5
    total_cars: int = 20
    sector_at_pit: str = "S2"


class StrategyOptimizeRequest(BaseModel):
    driver_id: str
    current_lap: int
    total_laps: int
    current_position: int
    tire_age: int
    tire_compound: str = "MEDIUM"
    degradation_rate: float = 0.002
    traffic_density: float = 0.5
    driver_pace: float = 95.0
    opponent_pace: Optional[float] = None


class DriverTwinUpdateRequest(BaseModel):
    driver_id: str
    lap_time: float
    sector_times: Dict[str, float]
    telemetry_data: Optional[Dict] = None
    tire_compound: str = "MEDIUM"
    current_lap: int = 1
    emit_to_nodejs: bool = True


# Strategy Console Request Models
class PitWindowTimelineRequest(BaseModel):
    driver_id: str
    current_lap: int
    total_laps: int
    tire_age: int
    tire_compound: str = "MEDIUM"
    degradation_rate: float = 0.002
    current_position: int = 1
    traffic_density: float = 0.5


class UndercutOvercutRequest(BaseModel):
    driver_id: str
    current_lap: int
    driver_pace: float
    opponent_pace: Optional[float] = None
    tire_age: int
    opponent_tire_age: int
    degradation_rate: float = 0.002
    traffic_density: float = 0.5
    current_position: int = 1
    opponent_position: int = 2


class RiskScoreRequest(BaseModel):
    tire_age: int
    degradation_rate: float
    traffic_density: float
    position: int
    laps_remaining: int
    tire_compound: str = "MEDIUM"


class TireLifeRequest(BaseModel):
    tire_age: int
    tire_compound: str
    degradation_rate: float
    track_temperature: float = 25.0
    driver_aggression: float = 0.5


class RejoinWindowRequest(BaseModel):
    driver_id: str
    current_position: int
    pit_lap: int
    traffic_density: float
    total_cars: int
    sector_at_pit: str = "S2"


# Track Map Request Models
class DriverPositionsRequest(BaseModel):
    drivers: List[Dict]
    current_lap: int
    sector: Optional[str] = None


class TrafficDensityRequest(BaseModel):
    drivers: List[Dict]
    sector: Optional[str] = None


class PitRejoinGhostRequest(BaseModel):
    driver_id: str
    current_position: int
    pit_lap: int
    drivers: List[Dict]
    traffic_density: float
    total_cars: int
    sector_at_pit: str = "S2"


class HeatmapRequest(BaseModel):
    drivers: List[Dict]
    resolution: int = 100


# Health check
@app.get('/')
async def root():
    return {
        'service': 'GR Race Guardian ML Service',
        'status': 'running',
        'version': '1.0.0'
    }


@app.get('/health')
async def health():
    return {'status': 'ok'}


# Prediction endpoint
@app.post('/predict')
async def predict_endpoint(req: PredictRequest):
    if not req.csv:
        raise HTTPException(status_code=400, detail='csv path is required')
    
    csv_path = req.csv if os.path.isabs(req.csv) else os.path.join('..', req.csv)
    
    if not req.model_path:
        raise HTTPException(status_code=400, detail='model_path required')
    
    try:
        model = load_model(req.model_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to load model: {e}')

    # Try to load metadata for feature names
    meta = load_model_meta(req.model_path)
    df = load_telemetry(csv_path, nrows=1)
    
    if req.features:
        feature_names = req.features
    elif meta and 'feature_names' in meta:
        feature_names = meta['feature_names']
    else:
        # Fallback: use numeric columns except last numeric which may be target
        nums = df.select_dtypes(include=['number']).columns.tolist()
        feature_names = nums[:-1] if len(nums) > 1 else nums

    X = []
    for f in feature_names:
        if f not in df.columns:
            X.append(0.0)
        else:
            X.append(float(df[f].fillna(0).iloc[0]))

    preds = predict(model, X)
    return {'prediction': preds, 'features_used': feature_names}


# Sector analysis endpoint
@app.post('/sectors/analyze')
async def analyze_sectors(req: SectorAnalysisRequest):
    try:
        csv_path = req.csv if os.path.isabs(req.csv) else os.path.join('..', req.csv)
        df = load_telemetry(csv_path)
        
        analysis = analyze_sector_performance(df, req.driver_id)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to analyze sectors: {str(e)}')


# Lap classification endpoint
@app.post('/laps/classify')
async def classify_laps(csv: str, driver_id: Optional[str] = None):
    try:
        csv_path = csv if os.path.isabs(csv) else os.path.join('..', csv)
        df = load_telemetry(csv_path)
        
        classified_df = classify_lap_dataframe(df)
        
        # Convert to JSON-serializable format
        result = classified_df.to_dict(orient='records')
        return {'laps': result, 'counts': classified_df['lap_type'].value_counts().to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to classify laps: {str(e)}')


# Driver metrics endpoint
@app.post('/driver/metrics')
async def get_driver_metrics(req: DriverMetricsRequest):
    try:
        csv_path = req.csv if os.path.isabs(req.csv) else os.path.join('..', req.csv)
        df = load_telemetry(csv_path)
        
        metrics = analyze_driver_performance(df, req.driver_id)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to calculate metrics: {str(e)}')


# Degradation analysis endpoint
@app.post('/degradation/analyze')
async def analyze_degradation(csv: str, driver_id: Optional[str] = None):
    try:
        csv_path = csv if os.path.isabs(csv) else os.path.join('..', csv)
        df = load_telemetry(csv_path)
        
        degradation_params = fit_degradation_from_data(df, driver_id)
        return degradation_params
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to analyze degradation: {str(e)}')


# Monte Carlo simulation endpoint
@app.post('/simulate')
async def simulate_race(req: MonteCarloRequest):
    try:
        results = simulate_race_strategy(
            req.driver_paces,
            n_laps=req.n_laps,
            iterations=req.iterations,
            pit_strategy=req.pit_strategy,
            compounds=req.compounds
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to simulate race: {str(e)}')


# Race pace prediction endpoint
@app.post('/pace/predict')
async def predict_pace(req: PacePredictionRequest):
    try:
        degradation_model = TireDegradationModel(req.compound, req.track_temp)
        predicted_time = degradation_model.linear_degradation(
            req.lap_number,
            req.base_lap_time
        )
        
        # Add fuel effect
        from grracing.degradation import FuelEffectModel
        fuel_model = FuelEffectModel()
        fuel_effect = fuel_model.calculate_fuel_effect(req.lap_number, req.fuel_load)
        
        predicted_time += fuel_effect
        
        return {
            'predicted_lap_time': round(predicted_time, 3),
            'base_lap_time': req.base_lap_time,
            'lap_number': req.lap_number,
            'degradation': round(predicted_time - req.base_lap_time - fuel_effect, 3),
            'fuel_effect': round(fuel_effect, 3)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to predict pace: {str(e)}')


# Pit window optimization endpoint
@app.post('/strategy/pit-window')
async def optimize_pit_window(
    base_lap_time: float,
    degradation_rate: float,
    pit_loss: float = 25.0,
    compound: str = "SOFT"
):
    try:
        degradation_model = TireDegradationModel(compound)
        pit_window = degradation_model.calculate_pit_window(
            base_lap_time,
            degradation_rate,
            pit_loss
        )
        return pit_window
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to calculate pit window: {str(e)}')


# Driver Twin endpoints
@app.get('/driver-twin/{driver_id}')
async def get_driver_twin(driver_id: str):
    """
    Get current Driver Twin for a driver.
    Note: In production, this would retrieve from database/cache.
    """
    # Placeholder - would fetch from storage in production
    return {
        "driver_id": driver_id,
        "message": "Driver Twin endpoint - use POST /driver-twin/update to generate",
        "note": "Store Driver Twin after generation for retrieval"
    }


@app.post('/driver-twin/update')
async def update_driver_twin(req: DriverTwinRequest):
    """
    Generate/update Driver Twin from lap data.
    """
    try:
        generator = DriverTwinGenerator()
        twin = generator.generate_driver_twin(
            driver_id=req.driver_id,
            lap_times=req.lap_times,
            sector_times=req.sector_times,
            telemetry_data=req.telemetry_data,
            tire_compound=req.tire_compound,
            current_lap=req.current_lap
        )
        return {
            "success": True,
            "driver_twin": twin
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to generate Driver Twin: {str(e)}')


# Race Twin endpoints
@app.post('/race-twin/simulate')
async def simulate_race_twin_endpoint(req: RaceTwinRequest):
    """
    Run Monte Carlo race simulation (Race Twin).
    Stores the result for later retrieval.
    """
    try:
        simulator = RaceTwinSimulator(num_simulations=req.num_simulations)
        race_twin = simulator.simulate_race(
            race_id=req.race_id,
            drivers=req.drivers,
            total_laps=req.total_laps,
            current_lap=req.current_lap,
            weather_data=req.weather_data,
            pit_strategy_options=req.pit_strategy_options
        )
        
        # Store race twin in cache
        race_twin_cache[req.race_id] = {
            "race_twin": race_twin,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "race_id": req.race_id,
            "current_lap": req.current_lap,
            "total_laps": req.total_laps
        }
        
        return {
            "success": True,
            "race_twin": race_twin
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to simulate Race Twin: {str(e)}')


@app.get('/race-twin/{race_id}')
async def get_race_twin(race_id: str):
    """
    Get current Race Twin for a race.
    Returns the most recently simulated Race Twin for this race.
    """
    try:
        if race_id in race_twin_cache:
            cached = race_twin_cache[race_id]
            return {
                "success": True,
                "race_twin": cached["race_twin"],
                "timestamp": cached["timestamp"],
                "race_id": cached["race_id"],
                "current_lap": cached.get("current_lap", 1),
                "total_laps": cached.get("total_laps", 50)
            }
        else:
            return {
                "success": False,
                "race_id": race_id,
                "message": f"No Race Twin found for {race_id}. Run POST /race-twin/simulate first."
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to get Race Twin: {str(e)}')


# Production ML Model endpoints
@app.post('/predict/lap')
async def predict_lap_time(req: LapTimePredictionRequest):
    """
    Predict future lap time using production ML model.
    """
    try:
        predictor = LapTimePredictor()
        result = predictor.predict(
            track_temp=req.track_temp,
            ambient_temp=req.ambient_temp,
            tire_age=req.tire_age,
            stint_number=req.stint_number,
            fuel_load=req.fuel_load,
            track_condition=req.track_condition,
            sector_times=req.sector_times,
            driver_pace_vector=req.driver_pace_vector,
            driver_consistency=req.driver_consistency,
            base_lap_time=req.base_lap_time
        )
        return {
            "success": True,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to predict lap time: {str(e)}')


@app.post('/predict/stint')
async def predict_stint(req: StintPredictionRequest):
    """
    Predict stint pace (multiple laps).
    """
    try:
        predictor = LapTimePredictor()
        degradation_model = ProductionTireDegradationModel()
        
        stint_predictions = []
        cumulative_time = 0.0
        current_fuel = req.fuel_load_start
        
        for lap in range(1, req.laps + 1):
            # Predict this lap
            lap_result = predictor.predict(
                track_temp=req.track_temp,
                ambient_temp=req.track_temp,
                tire_age=lap,
                stint_number=1,
                fuel_load=current_fuel,
                track_condition="dry",
                driver_pace_vector=req.driver_pace_vector,
                base_lap_time=req.base_lap_time
            )
            
            predicted_time = lap_result['predicted_lap_time']
            cumulative_time += predicted_time
            
            # Fuel burn (simplified: ~2.5kg per lap)
            fuel_per_lap = 2.5
            current_fuel = max(0, current_fuel - fuel_per_lap)
            
            stint_predictions.append({
                "lap": lap,
                "predicted_time": round(predicted_time, 3),
                "cumulative_time": round(cumulative_time, 3),
                "fuel_remaining": round(current_fuel, 1)
            })
        
        # Degradation analysis
        lap_times = [p['predicted_time'] for p in stint_predictions]
        tire_ages = list(range(1, req.laps + 1))
        degradation_params = degradation_model.fit_degradation_curve(
            lap_times, tire_ages, req.tire_compound
        )
        
        return {
            "success": True,
            "stint_laps": req.laps,
            "total_time": round(cumulative_time, 3),
            "average_lap_time": round(cumulative_time / req.laps, 3),
            "predictions": stint_predictions,
            "degradation_profile": degradation_params
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to predict stint: {str(e)}')


class StintOptimizeRequest(BaseModel):
    degradation_rate: float
    tire_compound: str = "MEDIUM"
    fuel_consumption_per_lap: float = 2.5
    total_fuel_capacity: float = 100.0
    traffic_density: float = 0.5
    track_temp: float = 25.0
    driver_fatigue_factor: float = 0.1
    current_lap: int
    total_laps: int
    pit_window_start: int = 15
    pit_window_end: int = 25


class MLDegradationRequest(BaseModel):
    tire_age: int
    tire_compound: str = "MEDIUM"
    track_temp: float = 25.0
    ambient_temp: float = 25.0
    track_surface: str = "smooth"
    driver_aggression: float = 0.5
    base_pace: float = 95.0


class MLTrafficLossRequest(BaseModel):
    cars_ahead: int
    sector: str = "S2"
    traffic_density: float = 0.5
    driver_position: int
    total_cars: int = 20
    track_type: str = "road_course"


@app.post('/predict/stint-optimize')
async def optimize_stint_length(req: StintOptimizeRequest):
    """
    Optimize stint length using ML model.
    """
    try:
        optimizer = StintLengthOptimizer()
        result = optimizer.optimize_stint_length(
            degradation_rate=req.degradation_rate,
            tire_compound=req.tire_compound,
            fuel_consumption_per_lap=req.fuel_consumption_per_lap,
            total_fuel_capacity=req.total_fuel_capacity,
            traffic_density=req.traffic_density,
            track_temp=req.track_temp,
            driver_fatigue_factor=req.driver_fatigue_factor,
            current_lap=req.current_lap,
            total_laps=req.total_laps,
            pit_window_start=req.pit_window_start,
            pit_window_end=req.pit_window_end
        )
        return {
            "success": True,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to optimize stint: {str(e)}')


@app.post('/predict/ml-degradation')
async def predict_ml_degradation(req: MLDegradationRequest):
    """
    Predict tire degradation using ML model.
    """
    try:
        model = MLTireDegradationModel()
        result = model.predict_degradation(
            tire_age=req.tire_age,
            tire_compound=req.tire_compound,
            track_temp=req.track_temp,
            ambient_temp=req.ambient_temp,
            track_surface=req.track_surface,
            driver_aggression=req.driver_aggression,
            base_pace=req.base_pace
        )
        return {
            "success": True,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to predict ML degradation: {str(e)}')


@app.post('/predict/ml-traffic-loss')
async def predict_ml_traffic_loss(req: MLTrafficLossRequest):
    """
    Predict traffic loss using ML model.
    """
    try:
        model = MLTrafficLossModel()
        result = model.predict_traffic_loss(
            cars_ahead=req.cars_ahead,
            sector=req.sector,
            traffic_density=req.traffic_density,
            driver_position=req.driver_position,
            total_cars=req.total_cars,
            track_type=req.track_type
        )
        return {
            "success": True,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to predict ML traffic loss: {str(e)}')


@app.post('/strategy/pit-decision')
async def get_pit_decision(req: PitDecisionRequest):
    """
    Get advanced AI pit decision recommendation with multi-factor analysis.
    
    Uses Advanced Pit Decision Engine with:
    - Multi-factor decision engine (degradation, traffic, raceTwin)
    - Confidence scoring system (0-1 scale)
    - Factor breakdown explanation JSON
    - Integration with Race Twin simulator
    """
    try:
        engine = AdvancedPitDecisionEngine()
        
        # Use Race Twin from request or cache
        race_twin = req.race_twin
        if not race_twin and req.race_id in race_twin_cache:
            race_twin = race_twin_cache[req.race_id]
        
        # Make advanced pit decision
        decision_result = engine.make_pit_decision(
            driver_id=req.driver_id,
            current_lap=req.current_lap,
            total_laps=req.total_laps,
            tire_age=req.tire_age,
            tire_compound=req.tire_compound,
            current_position=req.position,
            degradation_rate=req.degradation_rate,
            traffic_density=req.traffic_density,
            race_twin=race_twin,
            driver_twin=req.driver_twin,
            opponent_data=req.opponent_data,
            weather_data=req.weather_data
        )
        
        return {
            "success": True,
            **decision_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to get pit decision: {str(e)}')


# ML Model Training Endpoints
class ModelTrainRequest(BaseModel):
    features: List[List[float]]
    target: List[float]
    model_type: str  # "lap_time", "degradation", "traffic_loss", "stint_optimizer"
    test_size: float = 0.2
    save_model: bool = True


# Replay Endpoints
@app.get('/replay/telemetry/{track_id}')
async def get_replay_telemetry(track_id: str):
    """
    Get pre-loaded replay data for a track.
    """
    try:
        # Check for pre-calculated JSON first
        json_path = f"mock_gps_replay_{track_id}.json"
        if os.path.exists(json_path):
            import json
            with open(json_path, 'r') as f:
                return json.load(f)
        
        # Fallback to generating from default CSVs if available
        # This is just a placeholder logic
        return {
            "track_id": track_id,
            "message": "No pre-loaded replay found. Upload CSV to generate."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to get replay: {str(e)}')


@app.post('/replay/telemetry/{track_id}')
async def upload_replay_telemetry(track_id: str, file: UploadFile = File(...)):
    """
    Upload CSV and generate GPS replay data.
    """
    try:
        # Save uploaded file temporarily
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, file.filename)
        
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Parse and build replay
        from grracing.telemetry_parser import parse_telemetry
        replay_data = parse_telemetry(track_id, temp_path)
        
        # Clean up
        os.remove(temp_path)
        
        return replay_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to process replay: {str(e)}')



@app.post('/ml/train')
async def train_ml_model(req: ModelTrainRequest):
    """
    Train an ML model with provided data.
    
    Model types: "lap_time", "degradation", "traffic_loss", "stint_optimizer"
    """
    try:
        import numpy as np
        
        features = np.array(req.features)
        target = np.array(req.target)
        
        if req.model_type == "lap_time":
            model = LapTimePredictor()
            result = model.train(features, target, req.test_size, req.save_model)
        elif req.model_type == "degradation":
            model = MLTireDegradationModel()
            result = model.train(features, target, req.test_size, req.save_model)
        elif req.model_type == "traffic_loss":
            model = MLTrafficLossModel()
            result = model.train(features, target, req.test_size, req.save_model)
        elif req.model_type == "stint_optimizer":
            model = StintLengthOptimizer()
            result = model.train(features, target, req.test_size, req.save_model)
        else:
            raise HTTPException(status_code=400, detail=f'Unknown model type: {req.model_type}')
        
        return {
            "success": True,
            "model_type": req.model_type,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to train model: {str(e)}')


@app.get('/ml/models')
async def list_available_models():
    """
    List all available ML models and their status.
    """
    import os
    base_dir = os.path.dirname(__file__)
    models_dir = os.path.join(base_dir, "models")
    
    models = {
        "lap_time_predictor": {
            "path": os.path.join(models_dir, "lap_time_predictor.joblib"),
            "exists": os.path.exists(os.path.join(models_dir, "lap_time_predictor.joblib")),
            "type": "XGBoost/RandomForest"
        },
        "ml_tire_degradation": {
            "path": os.path.join(models_dir, "ml_tire_degradation.joblib"),
            "exists": os.path.exists(os.path.join(models_dir, "ml_tire_degradation.joblib")),
            "type": "XGBoost/GradientBoosting"
        },
        "ml_traffic_loss": {
            "path": os.path.join(models_dir, "ml_traffic_loss.joblib"),
            "exists": os.path.exists(os.path.join(models_dir, "ml_traffic_loss.joblib")),
            "type": "XGBoost/GradientBoosting"
        },
        "stint_optimizer": {
            "path": os.path.join(models_dir, "stint_optimizer.joblib"),
            "exists": os.path.exists(os.path.join(models_dir, "stint_optimizer.joblib")),
            "type": "XGBoost/GradientBoosting"
        }
    }
    
    return {
        "success": True,
        "models": models,
        "models_directory": models_dir
    }


# Pit rejoin simulator endpoint
@app.post('/strategy/pit-rejoin')
async def simulate_pit_rejoin(req: PitRejoinRequest):
    """
    Simulate pit stop rejoin and predict rejoin position.
    """
    try:
        simulator = PitRejoinSimulator()
        result = simulator.simulate_pit_rejoin(
            driver_id=req.driver_id,
            current_position=req.current_position,
            pit_lap=req.pit_lap,
            pit_time=req.pit_time,
            average_lap_time=req.average_lap_time,
            traffic_density=req.traffic_density,
            total_cars=req.total_cars,
            sector_at_pit=req.sector_at_pit
        )
        return {
            "success": True,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to simulate pit rejoin: {str(e)}')


# Driver Twin update loop endpoint
@app.post('/driver-twin/update-loop')
async def update_driver_twin_loop(req: DriverTwinUpdateRequest):
    """
    Update Driver Twin with new lap data (real-time loop).
    """
    try:
        loop = get_driver_twin_loop()
        twin = loop.update_driver_twin(
            driver_id=req.driver_id,
            lap_time=req.lap_time,
            sector_times=req.sector_times,
            telemetry_data=req.telemetry_data,
            tire_compound=req.tire_compound,
            current_lap=req.current_lap
        )
        
        # Emit to Node.js if requested
        if req.emit_to_nodejs:
            await loop.emit_to_nodejs(req.driver_id, twin)
        
        return {
            "success": True,
            "driver_twin": twin
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to update Driver Twin loop: {str(e)}')


@app.get('/driver-twin/loop/{driver_id}')
async def get_driver_twin_from_loop(driver_id: str):
    """
    Get current Driver Twin from update loop.
    """
    try:
        loop = get_driver_twin_loop()
        twin = loop.get_driver_twin(driver_id)
        if twin:
            return {
                "success": True,
                "driver_twin": twin
            }
        else:
            return {
                "success": False,
                "message": f"No Driver Twin found for {driver_id}"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to get Driver Twin: {str(e)}')


# Strategy optimizer endpoint
@app.post('/strategy/optimize')
async def optimize_strategy_endpoint(req: StrategyOptimizeRequest):
    """
    Optimize pit strategy with undercut/overcut analysis.
    """
    try:
        optimizer = StrategyOptimizer()
        result = optimizer.optimize_pit_strategy(
            driver_id=req.driver_id,
            current_lap=req.current_lap,
            total_laps=req.total_laps,
            current_position=req.current_position,
            tire_age=req.tire_age,
            tire_compound=req.tire_compound,
            degradation_rate=req.degradation_rate,
            traffic_density=req.traffic_density,
            driver_pace=req.driver_pace,
            opponent_pace=req.opponent_pace
        )
        return {
            "success": True,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to optimize strategy: {str(e)}')


# Strategy Console Endpoints
@app.post('/strategy/pit-window-timeline')
async def pit_window_timeline(req: PitWindowTimelineRequest):
    """
    Generate dynamic pit window timeline.
    """
    try:
        engine = StrategyConsoleEngine()
        timeline = engine.generate_pit_window_timeline(
            driver_id=req.driver_id,
            current_lap=req.current_lap,
            total_laps=req.total_laps,
            tire_age=req.tire_age,
            tire_compound=req.tire_compound,
            degradation_rate=req.degradation_rate,
            current_position=req.current_position,
            traffic_density=req.traffic_density
        )
        return {
            "success": True,
            **timeline
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to generate pit window timeline: {str(e)}')


@app.post('/strategy/undercut-overcut')
async def undercut_overcut_simulation(req: UndercutOvercutRequest):
    """
    Simulate undercut and overcut scenarios.
    """
    try:
        engine = StrategyConsoleEngine()
        simulation = engine.simulate_undercut_overcut(
            driver_id=req.driver_id,
            current_lap=req.current_lap,
            driver_pace=req.driver_pace,
            opponent_pace=req.opponent_pace,
            tire_age=req.tire_age,
            opponent_tire_age=req.opponent_tire_age,
            degradation_rate=req.degradation_rate,
            traffic_density=req.traffic_density,
            current_position=req.current_position,
            opponent_position=req.opponent_position
        )
        return {
            "success": True,
            **simulation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to simulate undercut/overcut: {str(e)}')


@app.post('/strategy/risk-score')
async def calculate_risk_score(req: RiskScoreRequest):
    """
    Calculate comprehensive risk score.
    """
    try:
        engine = StrategyConsoleEngine()
        risk = engine.calculate_risk_score(
            tire_age=req.tire_age,
            degradation_rate=req.degradation_rate,
            traffic_density=req.traffic_density,
            position=req.position,
            laps_remaining=req.laps_remaining,
            tire_compound=req.tire_compound
        )
        return {
            "success": True,
            **risk
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to calculate risk score: {str(e)}')


@app.post('/strategy/tire-life-prediction')
async def predict_tire_life(req: TireLifeRequest):
    """
    Predict remaining tire life.
    """
    try:
        engine = StrategyConsoleEngine()
        prediction = engine.predict_tire_life(
            tire_age=req.tire_age,
            tire_compound=req.tire_compound,
            degradation_rate=req.degradation_rate,
            track_temperature=req.track_temperature,
            driver_aggression=req.driver_aggression
        )
        return {
            "success": True,
            **prediction
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to predict tire life: {str(e)}')


@app.post('/strategy/rejoin-window')
async def calculate_rejoin_window(req: RejoinWindowRequest):
    """
    Calculate optimal rejoin window after pit stop.
    """
    try:
        engine = StrategyConsoleEngine()
        window = engine.calculate_rejoin_window(
            driver_id=req.driver_id,
            current_position=req.current_position,
            pit_lap=req.pit_lap,
            traffic_density=req.traffic_density,
            total_cars=req.total_cars,
            sector_at_pit=req.sector_at_pit
        )
        return {
            "success": True,
            **window
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to calculate rejoin window: {str(e)}')


# Track Map Endpoints
@app.get('/track/coordinates')
async def get_track_coordinates(track_name: Optional[str] = None):
    """
    Get track coordinate system.
    """
    try:
        engine = TrackMapEngine()
        coordinates = engine.get_track_coordinates(track_name=track_name)
        return {
            "success": True,
            **coordinates
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to get track coordinates: {str(e)}')


@app.post('/track/driver-positions')
async def project_driver_positions(req: DriverPositionsRequest):
    """
    Project driver positions onto track coordinate system.
    """
    try:
        engine = TrackMapEngine()
        positions = engine.project_driver_positions(
            drivers=req.drivers,
            current_lap=req.current_lap,
            sector=req.sector
        )
        return {
            "success": True,
            **positions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to project driver positions: {str(e)}')


@app.post('/track/traffic-density')
async def calculate_traffic_density(req: TrafficDensityRequest):
    """
    Calculate enhanced traffic density.
    """
    try:
        engine = TrackMapEngine()
        density = engine.calculate_traffic_density(
            drivers=req.drivers,
            sector=req.sector
        )
        return {
            "success": True,
            **density
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to calculate traffic density: {str(e)}')


@app.post('/track/pit-rejoin-ghost')
async def predict_pit_rejoin_ghost(req: PitRejoinGhostRequest):
    """
    Predict pit rejoin ghost driver position.
    """
    try:
        engine = TrackMapEngine()
        ghost = engine.predict_pit_rejoin_ghost(
            driver_id=req.driver_id,
            current_position=req.current_position,
            pit_lap=req.pit_lap,
            drivers=req.drivers,
            traffic_density=req.traffic_density,
            total_cars=req.total_cars,
            sector_at_pit=req.sector_at_pit
        )
        return {
            "success": True,
            **ghost
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to predict pit rejoin ghost: {str(e)}')


@app.post('/track/heatmap')
async def generate_heatmap(req: HeatmapRequest):
    """
    Generate traffic density heatmap.
    """
    try:
        engine = TrackMapEngine()
        heatmap = engine.generate_heatmap(
            drivers=req.drivers,
            resolution=req.resolution
        )
        return {
            "success": True,
            **heatmap
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to generate heatmap: {str(e)}')


# Track Data Endpoints
class TrackDataRequest(BaseModel):
    track_id: str
    race_id: str


@app.get('/tracks/available')
async def get_available_tracks():
    """
    Get list of available tracks with race data.
    """
    try:
        parser = get_track_parser()
        tracks = parser.get_available_tracks()
        
        # Always return at least the track definitions even if paths don't exist
        # This allows users to see all tracks in the dropdown
        if not tracks:
            # Return all tracks with default race if none found
            tracks = [
                {"id": "barber", "name": "Barber Motorsports Park", "races": [{"id": "race-1", "name": "Race 1", "path": ""}]},
                {"id": "cota", "name": "Circuit of the Americas", "races": [{"id": "race-1", "name": "Race 1", "path": ""}]},
                {"id": "indianapolis", "name": "Indianapolis Motor Speedway", "races": [{"id": "race-1", "name": "Race 1", "path": ""}]},
                {"id": "road-america", "name": "Road America", "races": [{"id": "race-1", "name": "Race 1", "path": ""}]},
                {"id": "sebring", "name": "Sebring International Raceway", "races": [{"id": "race-1", "name": "Race 1", "path": ""}]},
                {"id": "sonoma", "name": "Sonoma Raceway", "races": [{"id": "race-1", "name": "Race 1", "path": ""}]},
                {"id": "vir", "name": "Virginia International Raceway", "races": [{"id": "race-1", "name": "Race 1", "path": ""}]}
            ]
        
        return {
            "success": True,
            "tracks": tracks
        }
    except Exception as e:
        import traceback
        error_detail = f'failed to get tracks: {str(e)}\n{traceback.format_exc()}'
        print(f"[API Error] {error_detail}")
        # Return default tracks even on error
        return {
            "success": True,
            "tracks": [
                {"id": "barber", "name": "Barber Motorsports Park", "races": [{"id": "race-1", "name": "Race 1", "path": ""}]},
                {"id": "cota", "name": "Circuit of the Americas", "races": [{"id": "race-1", "name": "Race 1", "path": ""}]},
                {"id": "indianapolis", "name": "Indianapolis Motor Speedway", "races": [{"id": "race-1", "name": "Race 1", "path": ""}]},
                {"id": "road-america", "name": "Road America", "races": [{"id": "race-1", "name": "Race 1", "path": ""}]},
                {"id": "sebring", "name": "Sebring International Raceway", "races": [{"id": "race-1", "name": "Race 1", "path": ""}]},
                {"id": "sonoma", "name": "Sonoma Raceway", "races": [{"id": "race-1", "name": "Race 1", "path": ""}]},
                {"id": "vir", "name": "Virginia International Raceway", "races": [{"id": "race-1", "name": "Race 1", "path": ""}]}
            ],
            "error": str(e)
        }


@app.post('/tracks/results')
async def get_track_results(req: TrackDataRequest):
    """
    Get race results for a specific track and race.
    """
    try:
        parser = get_track_parser()
        results = parser.parse_race_results(req.track_id, req.race_id)
        return {
            "success": "error" not in results,
            **results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to get results: {str(e)}')


@app.post('/tracks/lap-times')
async def get_track_lap_times(req: TrackDataRequest):
    """
    Get lap times for a specific track and race.
    """
    try:
        parser = get_track_parser()
        lap_times = parser.parse_lap_times(req.track_id, req.race_id)
        return {
            "success": "error" not in lap_times,
            **lap_times
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to get lap times: {str(e)}')


@app.post('/tracks/replay')
async def get_race_replay(req: TrackDataRequest):
    """
    Get complete race replay data for visualization using REAL race data.
    """
    try:
        parser = get_track_parser()
        replay_data = parser.get_race_replay_data(req.track_id, req.race_id)
        return {
            "success": "error" not in replay_data,
            **replay_data
        }
    except Exception as e:
        import traceback
        error_detail = f'failed to get replay data: {str(e)}\n{traceback.format_exc()}'
        print(f"[API Error] {error_detail}")
        raise HTTPException(status_code=500, detail=f'failed to get replay data: {str(e)}')


@app.get('/tracks/{track_id}/coordinates')
async def get_track_coordinates_endpoint(track_id: str):
    """
    Get track coordinates and SVG path for visualization.
    """
    try:
        from grracing.track_coordinates import TrackCoordinates
        
        # Use class directly to avoid helper function issues
        coords_manager = TrackCoordinates()
        track_data = coords_manager.get_track_coordinates(track_id)
        
        if not track_data:
            raise HTTPException(status_code=404, detail=f'Track {track_id} not found')
            
        # Generate SVG path if not present
        if "svg_path" not in track_data and "coordinates" in track_data:
            try:
                # Simple path generation from coordinates
                points = track_data["coordinates"]
                if points:
                    path = f"M {points[0]['x']*1000} {points[0]['y']*1000}"
                    for p in points[1:]:
                        path += f" L {p['x']*1000} {p['y']*1000}"
                    path += " Z"
                    track_data["svg_path"] = path
            except Exception:
                pass
        
        return {
            "success": True,
            "track_id": track_id,
            **track_data
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[API Error] {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post('/tracks/{track_id}/lap/{lap_num}/positions')
async def get_lap_track_positions(track_id: str, lap_num: int, req: TrackDataRequest):
    """
    Get actual driver positions on track for a specific lap.
    """
    try:
        from grracing.real_race_replay import RealRaceReplay
        from grracing.track_data_parser import get_track_parser
        from grracing.track_coordinates import get_track_coordinates
        
        parser = get_track_parser()
        track_info = parser._get_track_info(track_id)
        
        if not track_info:
            raise HTTPException(status_code=404, detail=f'Track {track_id} not found')
        
        # Get replay data
        replay_data = parser.get_race_replay_data(track_id, req.race_id)
        if "error" in replay_data:
            raise HTTPException(status_code=404, detail=replay_data["error"])
        
        # Get track coordinates
        track_coords = get_track_coordinates()
        coords = track_coords.get_track_coordinates(track_id)
        
        # Calculate positions
        replay_engine = RealRaceReplay(parser.tracks_base_path)
        driver_positions = replay_engine.get_driver_track_positions(
            lap_num, 
            replay_data.get("lap_progression", []),
            coords.get("coordinates", []) if coords else []
        )
        
        return {
            "success": True,
            "lap": lap_num,
            "track_id": track_id,
            "driver_positions": driver_positions
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f'failed to get lap positions: {str(e)}\n{traceback.format_exc()}'
        print(f"[API Error] {error_detail}")
        raise HTTPException(status_code=500, detail=f'failed to get lap positions: {str(e)}')




# Race Replay Builder Endpoints
class ReplayBuildRequest(BaseModel):
    track_id: str
    race_id: str


@app.post('/replay/build')
async def build_race_replay(req: ReplayBuildRequest):
    """
    Build race replay JSON from CSV files.
    
    Analyzes lap times and results to create complete race timeline
    with overtakes, gaps, and position changes.
    """
    try:
        builder = RaceReplayBuilder(req.track_id)
        parser = get_track_parser()
        
        # Get track directory
        track_info = parser._get_track_info(req.track_id)
        if not track_info:
            raise HTTPException(status_code=404, detail=f'Track {req.track_id} not found')
        
        # Get track directory - convert to absolute path
        track_dir = track_info['path']
        
        # Convert to absolute path if it's relative
        import glob
        import os
        
        if not os.path.isabs(track_dir):
            # Get the base directory (where the backend is running from)
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            track_dir = os.path.join(base_dir, track_dir)
        
        print(f"[DEBUG] Searching in absolute path: {track_dir}")
        print(f"[DEBUG] Directory exists: {os.path.exists(track_dir)}")
        
        # Find CSV files
        results_csv = None
        lap_times_csv = None
        
        # Convert race_id to race number (race-1 -> 1, race-2 -> 2, R1 -> 1, etc.)
        race_num = req.race_id.replace('race-', '').replace('R', '').replace('r', '')
        
        # Search for results CSV
        # Pattern: 03_Provisional Results_Race 1_Anonymized.CSV or 03_Results*Race 1*.CSV
        # Search recursively to handle "Race 1" subfolders
        results_pattern = os.path.join(track_dir, "**", "03_*Results*.CSV")
        print(f"[DEBUG] Results pattern: {results_pattern}")
        
        results_candidates = glob.glob(results_pattern, recursive=True)
        # Also try non-recursive if recursive returns nothing (though ** should cover it)
        if not results_candidates:
             results_candidates = glob.glob(os.path.join(track_dir, "03_*Results*.CSV"))

        for file in results_candidates:
            print(f"[DEBUG] Checking results file: {file}")
            # Check if file contains "Race 1" or "Race 2"
            # Also check if parent folder is "Race 1" or "Race 2"
            file_path_lower = file.lower().replace('\\', '/')
            race_str = f"race {race_num}"
            race_str_short = f"race{race_num}"
            
            if race_str in file_path_lower or race_str_short in file_path_lower:
                results_csv = file
                print(f"[DEBUG] ✓ Found results CSV: {file}")
                break
        
        # Search for lap times CSV
        # Pattern: R1_barber_lap_time.csv or R2_barber_lap_time.csv
        lap_times_pattern = os.path.join(track_dir, "**", "*lap_time.csv")
        print(f"[DEBUG] Lap times pattern: {lap_times_pattern}")
        
        lap_candidates = glob.glob(lap_times_pattern, recursive=True)
        if not lap_candidates:
            lap_candidates = glob.glob(os.path.join(track_dir, "*lap_time.csv"))

        for file in lap_candidates:
            print(f"[DEBUG] Checking lap time file: {file}")
            # Check for R1_, R2_, etc.
            filename = os.path.basename(file)
            if f"R{race_num}_" in filename or f"r{race_num}_" in filename:
                lap_times_csv = file
                print(f"[DEBUG] ✓ Found lap times CSV: {file}")
                break
        
        if not results_csv or not lap_times_csv:
            # Provide helpful error message with actual files found
            available_results = list(glob.glob(os.path.join(track_dir, "03_*.CSV")))
            available_laps = list(glob.glob(os.path.join(track_dir, "*lap_time.csv")))
            
            error_msg = f'CSV files not found for {req.track_id} race {race_num}.\n'
            error_msg += f'Searched in: {track_dir}\n'
            error_msg += f'Directory exists: {os.path.exists(track_dir)}\n'
            error_msg += f'Found {len(available_results)} results files: {[os.path.basename(f) for f in available_results[:3]]}\n'
            error_msg += f'Found {len(available_laps)} lap time files: {[os.path.basename(f) for f in available_laps[:3]]}'
            
            raise HTTPException(status_code=404, detail=error_msg)

        
        # Build replay
        replay_data = builder.build_replay_json(results_csv, lap_times_csv)
        
        return {
            "success": True,
            **replay_data
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f'failed to build replay: {str(e)}\n{traceback.format_exc()}'
        print(f"[API Error] {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get('/replay/tracks')
async def get_replay_tracks():
    """
    Get list of tracks with available replay data.
    """
    try:
        parser = get_track_parser()
        tracks = parser.get_available_tracks()
        
        return {
            "success": True,
            "tracks": tracks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/replay/telemetry/{track_id}')
async def get_telemetry_replay(track_id: str, race: str = 'R1'):
    """
    Get GPS telemetry replay data for a track.
    Reads lap timing CSV from the track folder and generates GPS positions.
    
    Args:
        track_id: Track identifier (e.g., 'barber', 'road-america')
        race: Race identifier (default: 'R1')
    """
    try:
        from grracing.telemetry_parser import TelemetryParser
        import os
        
        # Map track IDs to folder names
        track_folder_map = {
            'barber': 'barber-motorsports-park',
            'road-america': 'road-america',
            'sebring': 'sebring',
            'indianapolis': 'indianapolis',
            'sonoma': 'sonoma',
            'vir': 'vir',
            'cota': 'cota',
            'laguna-seca': 'laguna-seca'
        }
        
        # Get folder name
        folder_name = track_folder_map.get(track_id, track_id)
        
        # Build path to lap times CSV
        base_path = os.path.dirname(os.path.dirname(__file__))
        
        # Try different path patterns
        possible_paths = [
            os.path.join(base_path, folder_name, track_id, f'{race}_{track_id.replace("-", "_")}_lap_time.csv'),
            os.path.join(base_path, folder_name, track_id.split('-')[0], f'{race}_{track_id.replace("-", "_")}_lap_time.csv'),
            os.path.join(base_path, folder_name, 'barber', f'{race}_barber_lap_time.csv'),  # Barber specific
        ]
        
        lap_times_path = None
        for path in possible_paths:
            if os.path.exists(path):
                lap_times_path = path
                break
        
        if not lap_times_path:
            # Return mock data if file not found
            print(f"[INFO] Lap times CSV not found for {track_id}, returning mock data")
            from grracing.telemetry_parser import TelemetryParser
            parser = TelemetryParser(track_id)
            
            # Generate simple mock replay
            track_path_gps = parser.build_track_path_gps()
            track_gps = parser.gps_coords.get_track_gps(track_id)
            track_info = parser.track_coords.get_track_coordinates(track_id)
            
            # Create mock frames with 5 cars
            frames = []
            for time_sec in range(0, 300, 2):  # 5 minutes, 2 second intervals
                frame = {
                    'timestamp': f'2024-01-01T00:{time_sec//60:02d}:{time_sec%60:02d}Z',
                    'time_seconds': time_sec,
                    'cars': []
                }
                
                for car_num in range(1, 6):
                    lap_progress = ((time_sec + car_num * 10) % 90) / 90
                    lat, lon = parser.calculate_track_position(lap_progress)
                    
                    frame['cars'].append({
                        'vehicle_number': car_num,
                        'lap': (time_sec // 90) + 1,
                        'lap_progress': lap_progress,
                        'position': {'lat': lat, 'lon': lon}
                    })
                
                frames.append(frame)
            
            return {
                'success': True,
                'track_id': track_id,
                'track_name': track_info.get('name', 'Unknown'),
                'track_gps': track_gps,
                'track_path': [{'lat': lat, 'lon': lon} for lat, lon in track_path_gps],
                'duration_seconds': 300,
                'frames': frames,
                'vehicles': list(range(1, 6)),
                'data_source': 'mock'
            }
        
        # Parse actual lap times and generate replay
        print(f"[INFO] Loading lap times from: {lap_times_path}")
        parser = TelemetryParser(track_id)
        replay_data = parser.build_telemetry_replay(lap_times_path)
        replay_data['success'] = True
        replay_data['data_source'] = 'actual'
        
        return replay_data
        
    except Exception as e:
        import traceback
        error_detail = f'failed to get telemetry replay: {str(e)}\n{traceback.format_exc()}'
        print(f"[API Error] {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))





if __name__ == '__main__':

    import uvicorn
    uvicorn.run('app:app', host='0.0.0.0', port=8000, reload=False)
