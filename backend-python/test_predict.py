import os
import sys
import json
import joblib
try:
    from fastapi.testclient import TestClient
except Exception:
    TestClient = None

# ensure backend-python is on sys.path so `import grracing` works
backend_pkg = os.path.abspath(os.path.dirname(__file__))
if backend_pkg not in sys.path:
    sys.path.insert(0, backend_pkg)
from grracing.models import load_model_meta, load_model

# Direct model test
model_path = os.path.join(backend_pkg, 'models', 'merged_road_model.joblib')
merged_csv = os.path.join(backend_pkg, 'models', 'merged_road_america.csv')

print('Model path exists?', os.path.exists(model_path))
print('Merged CSV exists?', os.path.exists(merged_csv))

if os.path.exists(model_path):
    model = load_model(model_path)
    meta = load_model_meta(model_path)
    features = meta['feature_names'] if meta else None
    print('Loaded model; features:', features)
    if features and os.path.exists(merged_csv):
        import pandas as pd
        df = pd.read_csv(merged_csv)
        sample = df[features].fillna(0).iloc[0].tolist()
        print('Sample features (first row):', sample)
        # predict expects model and X list
        from grracing.models import predict
        pred = predict(model, sample)
        print('Direct prediction result:', pred)

# FastAPI endpoint test using TestClient (optional)
if TestClient is not None:
    try:
        from app import app
        client = TestClient(app)
        payload = {
            'csv': merged_csv,
            'model_path': model_path
        }
        print('Calling FastAPI /predict endpoint...')
        resp = client.post('/predict', json=payload)
        print('Status code:', resp.status_code)
        print('Response JSON:', resp.json())
    except Exception as e:
        print('Skipping FastAPI endpoint test due to import/run error:', e)
else:
    print('Skipping FastAPI endpoint test because TestClient is not available in this environment')

print('Test script completed')
