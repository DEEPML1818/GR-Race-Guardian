# 🚀 GR Race Guardian - Quick Startup Guide

## Prerequisites

1. **Python 3.8+** installed and on PATH
2. **Node.js 18+** installed and on PATH
3. **npm** (comes with Node.js)

## Installation

### 1. Install Python Dependencies

```cmd
cd backend-python
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Install Node.js Dependencies

```cmd
cd backend-node
npm install
```

```cmd
cd frontend-next
npm install
```

## Quick Start (All-in-One)

### Windows Batch File

```cmd
start_all.bat
```

This will:
- Start Python FastAPI service (port 8000)
- Start Node.js API service (port 3001)
- Start Next.js Frontend (port 3000)
- Open frontend in browser

### PowerShell Script

```powershell
.\start_all.ps1
```

## Manual Start (Step-by-Step)

### 1. Start Python FastAPI Service

Open a terminal:

```cmd
cd backend-python
python app.py
```

Service will run on: `http://localhost:8000`

### 2. Start Node.js API Service

Open another terminal:

```cmd
cd backend-node
npm install
node server.js
```

Service will run on: `http://localhost:3001`

### 3. Start Frontend

Open another terminal:

```cmd
cd frontend-next
npm install
npm run dev
```

Frontend will run on: `http://localhost:3000`

## Using the Application

1. **Open Frontend**: Navigate to `http://localhost:3000`
2. **Start Race Simulation**: Click "▶️ Start Race Simulation" button
3. **View Live Updates**: Watch real-time race updates in the dashboard
4. **View Charts**: See lap times and delta charts update in real-time

## API Endpoints

### Python FastAPI (Port 8000)

- `GET /` - Health check
- `GET /health` - Health status
- `POST /predict` - Make predictions
- `POST /sectors/analyze` - Analyze sector performance
- `POST /laps/classify` - Classify laps
- `POST /driver/metrics` - Get driver metrics
- `POST /simulate` - Run Monte Carlo simulation
- `POST /pace/predict` - Predict race pace

### Node.js API (Port 3001)

- `GET /health` - Health check
- `POST /api/predict` - Make predictions (proxy to Python)
- `POST /api/race/start` - Start race simulation
- `POST /api/race/stop` - Stop race simulation
- `POST /api/driver/metrics` - Get driver metrics
- `POST /api/simulate` - Run simulation
- WebSocket: `ws://localhost:3001` - Real-time race updates

## Troubleshooting

### Port Already in Use

If you get "port already in use" errors:

1. **Python API (8000)**: Change port in `backend-python/app.py`:
   ```python
   uvicorn.run('app:app', host='0.0.0.0', port=8000)
   ```

2. **Node.js API (3001)**: Change port in `backend-node/server.js`:
   ```javascript
   const PORT = process.env.PORT || 3001;
   ```

3. **Frontend (3000)**: Change port in `frontend-next/package.json`:
   ```json
   "dev": "next dev -p 3000"
   ```

### Dependencies Not Found

Make sure all dependencies are installed:

```cmd
cd backend-python
pip install -r requirements.txt

cd ../backend-node
npm install

cd ../frontend-next
npm install
```

### WebSocket Connection Issues

1. Check that Node.js API is running on port 3001
2. Check browser console for WebSocket errors
3. Verify CORS settings in `backend-node/server.js`

## Next Steps

- See [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md) for feature development
- See [TECH_STACK.md](TECH_STACK.md) for technology stack details
- See [QUICK_START.md](QUICK_START.md) for first feature implementation guide

## Stopping Services

- **Windows**: Close the terminal windows where services are running
- **Batch File**: Press Ctrl+C in each service window
- **Or**: Kill processes:
  ```cmd
  taskkill /F /IM node.exe
  taskkill /F /IM python.exe
  ```

---

**Ready to race! 🏎️**

