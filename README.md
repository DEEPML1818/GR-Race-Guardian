# 🏎️ GR Race Guardian

**Professional Motorsport Analytics Platform**

Real-time race analysis, AI-powered insights, and predictive modeling for motorsport teams and enthusiasts.

---

## 📖 What Is This?

GR Race Guardian is a comprehensive racing analytics platform that provides:

- **Real-time race dashboards** with live updates
- **AI race engineer** with 7 analysis modes
- **Machine learning predictions** for lap times, tire degradation, and race outcomes
- **Strategy optimization** with pit window recommendations
- **Driver analytics** comparing performance metrics
- **Professional-grade insights** using motorsport industry standards

Think of it as having a **digital race engineer** analyzing your race in real-time!

---

## ✨ Key Features

### 🎯 Real-Time Analysis
- Live WebSocket updates every second
- Real-time lap times, positions, and sector splits
- Live telemetry visualization
- Driver statistics dashboard

### 🤖 AI Race Engineer (7 Modes)
- **Engineering** - Professional race engineering insights
- **Strategy** - Real-time tactical recommendations  
- **Coach** - Driver improvement analysis
- **Fan** - Exciting race storytelling
- **Summary** - Race recap and highlights
- **Compare** - Side-by-side driver comparison
- **Pit Decision** - Should we pit now? (AI recommendations)

### 📊 Advanced Components
- **Strategy Console** - Pit strategy visualization
- **Traffic Rejoin Map** - Sector-by-sector traffic density
- **Live Pit Decision Panel** - Real-time pit recommendations
- **Multi-Driver Comparison** - Performance analysis with radar charts

### 🔮 Machine Learning
- Lap time prediction
- Tire degradation modeling
- Race pace optimization
- Monte Carlo race simulation
- Overtake probability calculation
- Traffic density analysis
- Weather effects modeling

### 📈 Driver Analytics
- Consistency Index
- Aggression Score
- Sector Strength Analysis
- Pace Vector
- Fatigue Performance Dropoff

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- npm/yarn

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd gr-race-guardian
   ```

2. **Install Dependencies**

   **Backend (Node.js)**:
   ```bash
   cd backend-node
   npm install
   ```

   **Backend (Python)**:
   ```bash
   cd backend-python
   pip install -r requirements.txt
   ```

   **Frontend**:
   ```bash
   cd frontend-next
   npm install
   ```

3. **Start All Services**

   **Windows**:
   ```bash
   start_all.bat
   ```

   **Linux/Mac**:
   ```bash
   # Terminal 1: Python Backend
   cd backend-python
   python app.py

   # Terminal 2: Node.js Backend
   cd backend-node
   node server.js

   # Terminal 3: Frontend
   cd frontend-next
   npm run dev
   ```

4. **Access the Application**
   - **Dashboard**: http://localhost:3000
   - **Python API**: http://localhost:8000
   - **Node.js API**: http://localhost:3001

5. **Login**
   - Default: `admin` / `admin123`
   - Or create a new account

---

## 📚 Documentation

- **[APP_SUMMARY.md](APP_SUMMARY.md)** - What the app does (detailed overview)
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment guide (Vercel, Railway, Render)
- **[DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md)** - Complete feature roadmap
- **[ROADMAP_STATUS.md](ROADMAP_STATUS.md)** - Implementation status (98% complete!)
- **[AI_AGENT.md](AI_AGENT.md)** - GR-RACE-GUARDIAN-AI documentation
- **[START_HERE.md](START_HERE.md)** - Quick start guide

---

## 🏗️ Architecture

### Backend Services
- **Python FastAPI** (`backend-python/`) - ML models, racing analytics
- **Node.js Express** (`backend-node/`) - API, WebSocket, AI agent
- **WebSocket** - Real-time race updates
- **Bull Queue** (optional) - Job queue for heavy processing

### Frontend
- **Next.js** (`frontend-next/`) - React dashboard
- **Recharts** - Chart visualizations
- **Plotly.js** - Telemetry graphs
- **Tailwind CSS** - Styling

### Storage
- **JSON-based** - Lightweight file storage
- **SQLite-ready** - Easy migration path

---

## 🎯 Use Cases

### For Race Teams
- Real-time race engineering during live races
- Strategy optimization and pit window planning
- Driver coaching based on performance data
- Traffic management for endurance races

### For Drivers
- Performance analysis and improvement areas
- Sector analysis for optimizing driving lines
- Consistency tracking and pace analysis

### For Enthusiasts
- Live race monitoring with professional insights
- AI-generated race commentary
- Driver comparisons and strategy analysis

---

## 🔧 Tech Stack

### Core
- **Python** - Machine learning, data analysis
- **Node.js** - Real-time API, WebSocket server
- **React/Next.js** - Frontend dashboard

### Machine Learning
- **XGBoost** - Predictive models
- **scikit-learn** - ML algorithms
- **NumPy/SciPy** - Numerical analysis
- **SHAP** - Model explainability

### Racing Analytics
- **Sector Timing Engine** - FIA-style sector analysis
- **Lap Classification** - OUT/IN/HOT/COOL/PIT laps
- **Driver Metrics** - Consistency, aggression, pace
- **Degradation Modeling** - Tire wear analysis
- **Monte Carlo Simulation** - Race strategy testing

---

## 📊 API Endpoints

### Node.js API (`localhost:3001`)
- `GET /health` - Health check
- `POST /api/race/start` - Start race simulation
- `POST /api/race/stop` - Stop race simulation
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `POST /api/ai/analyze` - AI analysis
- `POST /api/jobs/simulate` - Queue simulation job
- `GET /api/jobs/stats` - Queue statistics
- WebSocket: Real-time race updates

### Python API (`localhost:8000`)
- `GET /health` - Health check
- `POST /predict` - ML predictions
- `POST /sectors/analyze` - Sector analysis
- `POST /driver/metrics` - Driver metrics
- `POST /simulate` - Monte Carlo simulation
- `POST /pace/predict` - Race pace prediction

---

## 🎮 Features Overview

### Dashboard Tabs

1. **Dashboard** 📊
   - Live race updates
   - Driver statistics
   - Real-time charts
   - Update history

2. **Strategy** 🎯
   - Pit window recommendations
   - AI pit decisions
   - Strategy risks
   - Stint analysis

3. **Comparison** 📈
   - Multi-driver comparison
   - Sector strength radar
   - Lap-by-lap analysis
   - Metrics table

---

## 🚀 Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment guide.

**Quick Deploy Options:**
- **Vercel** - Frontend deployment
- **Railway** - Backend deployment
- **Render** - Alternative hosting
- **Docker** - Container deployment

---

## 🔐 Authentication

- JWT-based authentication
- User registration and login
- Protected API routes
- Admin role support

**Default Credentials:**
- Username: `admin`
- Password: `admin123`

---

## 📈 Status

**98% Complete** - All core features implemented!

- ✅ Real-time WebSocket updates
- ✅ Frontend visualizations
- ✅ ML models (XGBoost)
- ✅ AI agent (7 modes)
- ✅ Authentication system
- ✅ Advanced frontend components
- ✅ Bull Queue system
- ✅ Deployment guides

---

## 🤝 Contributing

This is a complete platform. All features from the development roadmap are implemented!

---

## 📝 License

[Your License Here]

---

## 🙏 Acknowledgments

Built with professional motorsport analytics standards in mind.

---

**Ready to analyze your race? Run `start_all.bat` and start your race! 🏎️✨**

For detailed information about what the app does, see [APP_SUMMARY.md](APP_SUMMARY.md)
