# Backend Python (ML Engine)

This subfolder contains a minimal ML engine for loading telemetry CSVs, training a simple model, and serving predictions via CLI.

Files:
- `grracing/data.py` — CSV loader helpers
- `grracing/models.py` — training & predict utilities
- `train.py` — CLI example to train a model
- `serve_model.py` — simple CLI predictor (used by Node backend)

Typical usage (Windows cmd.exe):
```cmd
cd backend-python
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python train.py --csv "..\..\barber-motorsports-park\barber\R1_barber_lap_time.csv" --out models/model.joblib
python serve_model.py --csv "..\..\barber-motorsports-park\barber\R1_barber_lap_time.csv"
```

New features in this scaffold:
- `app.py` — FastAPI microservice: run with `uvicorn app:app --reload --port 8000` and POST JSON `{ "csv": "<path>", "model_path": "models/road_america_model.joblib" }` to `/predict`.
- `grracing/preprocess.py` — helper to merge lap_time + telemetry, and CLI `preprocess.py`.
- `montecarlo.py` — simple Monte Carlo race simulator demo.
- gRPC: `infra/predict.proto`, `backend-python/grpc_server.py` and `backend-node/grpc_client.js` show a basic gRPC example. Generate Python gRPC modules with `python -m grpc_tools.protoc -I infra --python_out=. --grpc_python_out=. infra/predict.proto`.
