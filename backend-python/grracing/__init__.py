# grracing package - Professional motorsport analytics

from .data import load_telemetry
# Import from models.py file (not models/ package)
# Use importlib to avoid conflict with models/ directory
import importlib.util
import os

# Load models.py as a module to avoid conflict with models/ package
_models_file_path = os.path.join(os.path.dirname(__file__), 'models.py')
_models_spec = importlib.util.spec_from_file_location("grracing._models", _models_file_path)
_models_module = importlib.util.module_from_spec(_models_spec)
_models_spec.loader.exec_module(_models_module)

# Import functions from models.py
load_model = _models_module.load_model
load_model_meta = _models_module.load_model_meta
predict = _models_module.predict
train_simple_model = _models_module.train_simple_model

from .preprocess import merge_lap_and_telemetry

# Racing-specific modules
from .sector_timing import SectorTimingEngine, analyze_sector_performance
from .lap_classification import LapClassifier, LapType, classify_lap_dataframe
from .driver_metrics import DriverMetrics, analyze_driver_performance
from .degradation import TireDegradationModel, FuelEffectModel, fit_degradation_from_data
from .monte_carlo import MonteCarloRaceSimulator, simulate_race_strategy
from .weather import WeatherModel, load_weather_from_csv
from .overtake import OvertakeProbabilityModel
from .traffic import TrafficDensityModel
from .driver_twin import DriverTwinGenerator, generate_driver_twin_json
from .race_twin import RaceTwinSimulator, simulate_race_twin
# Import from models/ package (production ML models)
from .models.lap_time_predictor import LapTimePredictor
from .models.tire_degradation import TireDegradationModel as ProductionTireDegradationModel
from .models.traffic_loss import TrafficLossModel

__all__ = [
    # Data loading
    'load_telemetry',
    # Models
    'load_model',
    'load_model_meta',
    'predict',
    'train_simple_model',
    # Preprocessing
    'merge_lap_and_telemetry',
    # Sector timing
    'SectorTimingEngine',
    'analyze_sector_performance',
    # Lap classification
    'LapClassifier',
    'LapType',
    'classify_lap_dataframe',
    # Driver metrics
    'DriverMetrics',
    'analyze_driver_performance',
    # Degradation
    'TireDegradationModel',
    'FuelEffectModel',
    'fit_degradation_from_data',
    # Monte Carlo simulation
    'MonteCarloRaceSimulator',
    'simulate_race_strategy',
    # Weather modeling
    'WeatherModel',
    'load_weather_from_csv',
    # Overtake probability
    'OvertakeProbabilityModel',
    # Traffic density
    'TrafficDensityModel',
    # Driver Twin
    'DriverTwinGenerator',
    'generate_driver_twin_json',
    # Race Twin
    'RaceTwinSimulator',
    'simulate_race_twin',
    # Production ML Models
    'LapTimePredictor',
    'ProductionTireDegradationModel',
    'TrafficLossModel',
]