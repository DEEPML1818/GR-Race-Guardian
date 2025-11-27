# 🏎️ GR Race Guardian — Complete Tech Stack

This document outlines the comprehensive technology stack for GR Race Guardian, a professional-grade motorsport analytics platform inspired by F1, WEC, IndyCar, and IMSA race engineering systems.

---

## 🧠 1. CORE PROGRAMMING STACK

### Backend Languages

| Layer | Language | Reason |
|-------|----------|--------|
| Machine Learning Engine | Python | pandas, sklearn, XGBoost, SciPy, NumPy, SHAP |
| Backend API + Realtime | Node.js (JavaScript) | Express, WebSockets |
| Frontend UI | Next.js + React | RaceWatch-style dashboards |

---

## 🔥 2. MACHINE LEARNING & AI STACK (Python)

### For Digital Driver Twin + Race Simulator + Predictions

#### ML Frameworks
- **scikit-learn** – regression, classification, calibration
- **XGBoost / LightGBM** – high-performance gradient boosting models
- **PyTorch** (optional) – for deep learning models
- **statsmodels** – statistical modeling for tire degradation curves

#### Data Science Libraries
- **pandas** – CSV/telemetry/sector merging
- **numpy** – vectorized lap/sector operations
- **SciPy** – curve fitting for degradation modeling

#### Explainability
- **SHAP** – feature importance, explainable strategy
- **LIME** (optional) – local interpretability

#### Prediction Models
- Pace model
- Degradation model
- Mistake probability
- Tire dropoff modeling
- Race finishing prediction

---

## 🏎️ 3. RACING-INDUSTRY TECH STACK (VERY IMPORTANT)

These are **REAL motorsport analysis tools** used in F1, WEC, IndyCar, NASCAR, IMSA, GT3, etc.

### Telemetry / Simulation / Data Handling
- **Motec** (optional export) – industry-standard telemetry
- **CAN bus data formats** (not required, but mention-ready)
- **Race chrono / AIM CSV format** compatibility
- **Sector timing engine** (FIA-style)
- **Monte Carlo simulation** for race strategy
- **Race Pace Modeling** (common in Formula teams)
- **Pit Window Optimization Algorithm**
- **Virtual Safety Car / Full Safety Car** modelling
- **Delta-to-Leader / Delta-to-Apex** timing logic
- **Traffic density modelling** (as used in endurance racing)
- **Overtake probability model** (motorsport ML research standard)
- **Regression-to-Track-Temperature** modeling

### Motorsport Data Engineering Concepts

#### Lap Classification
- **OUT LAP**
- **IN LAP**
- **HOT LAP**
- **COOL LAP**
- **ERROR LAP**
- **PIT LAP**

#### Driver Behaviour Metrics
- **Consistency Index**
- **Driving Aggression Score**
- **Pace Stability Curve**
- **Fatigue Performance Dropoff**
- **Sector Strength Fingerprint**

*Using these terms earns MASSIVE respect in Toyota's motorsport analytics circles.*

---

## ⚙️ 4. PYTHON RACE SIMULATION STACK

For Digital Race Twin + Real-Time Engineering Mode

- **NumPy** – vectorized simulation loops
- **Numba** (optional) – accelerate lap simulation
- **SimPy** – for discrete-event simulation
- **PySwarms** – optimization (optional)
- **custom Monte Carlo engine** – race scenarios
- **SciPy optimize** – pit strategy optimization

### Simulation includes:
- Strategy Monte Carlo
- Overtake probability
- Tire wear curve
- Pit stop loss modelling
- Fuel burn modelling (optional)
- Traffic density simulation
- Weather-influenced pace modelling

---

## 🌐 5. BACKEND STACK (JavaScript)

### Node.js + Express
- run analysis events
- communicate with Python engine
- serve REST + WebSocket APIs
- handle live race updates
- unify predictions + strategies
- caching + snapshot storage

### Inter-process Communication
- **child_process.spawn()** or
- **gRPC** (optional, enterprise-level)
- **ZeroMQ** (optional for low-latency)
- **REST endpoints** for simplicity

### Job Queue (recommended)
- **Bull Queue** or **BullMQ**
  - To manage:
    - heavy Python jobs
    - simulation tasks
    - sequential analysis
    - debounced messages (live mode)

---

## 💻 6. FRONTEND UI STACK (JavaScript / React)

### Frameworks
- **Next.js** (best for dashboards)
- **React**
- **Tailwind CSS**
- **Framer Motion** (animation like RaceWatch)
- **Zustand** or **Redux** (state management)

### Visualization Libraries
- **Recharts** – lap charts, gap charts
- **D3.js** – advanced custom racing maps
- **Plotly.js** – telemetry graphs
- **Three.js** (optional 3D car movement)
- **Visx** – performance charts

### RaceWatch-style UI components:
- Strategy console
- Traffic rejoin map
- Sector heatmap
- Pace trace
- Delta-to-leader graph
- Live pit decision panel
- Multi-driver comparison screen

---

## ☁️ 7. CLOUD / DEVOPS STACK

(optional but amazing for Devpost)

### Hosting
- **Vercel** (Next.js)
- **Render / Railway** (Node + Python)
- **AWS** (Lambda + EC2)
- **DigitalOcean**

### Storage
- **S3** (CSV/PDF uploads + snapshots)
- **SQLite** (simple)
- **PostgreSQL** (advanced)

### CI/CD
- **GitHub Actions**
  - Python model evaluation CI
  - JS lint + tests

---

## 📦 8. DATA PIPELINE & STORAGE STACK

### Data Storage Formats
- **JSON snapshots**
- **CSV raw telemetry**
- **Parquet** (optional, for large datasets)

### Data Versioning
- **DVC** (Data Version Control)
- local versioning (timestamped snapshots)

---

## 💬 9. AI Commentary + Narrative Stack

### LLM Providers (Choose 1)
- **OpenAI GPT-4o / GPT-5**
- **Anthropic Claude 3.5**
- **Gemini 2.0**

### Format
- Use Python analysis → Node prompt builder → LLM explanation.
- **LLM is not used for decisions.**
- LLM is used for:
  - coaching narrative
  - race summary
  - highlight storyteller
  - pit-wall explanations

---

## 🔒 10. SECURITY & PERFORMANCE STACK

- Rate limiting (express-rate-limit)
- JWT auth (optional)
- CORS
- Heavy Python jobs isolated via workers
- Cache predictions for each session
- Snapshot everything

---

## 🎮 11. OPTIONAL GAMING / FAN-MODE STACK

If you want advanced visualizations:
- **Unity WebGL** (3D replay)
- **Three.js** (3D track & car simulation)
- **Spline** (3D low-code assets)

---

## 🚀 COMPLETE FINAL TECH STACK LIST (READY TO COPY/PASTE)

### Languages
- Python
- JavaScript / TypeScript

### Python ML & Data
- pandas
- numpy
- scipy
- scikit-learn
- XGBoost
- LightGBM (optional)
- statsmodels
- SHAP
- PyTorch (optional)
- Numba (optional)
- SimPy

### Racing Tech
- Lap classification engine
- Sector timing engine
- Degradation curve modelling
- Overtake probability modelling
- Monte Carlo race simulation
- Tire wear modelling
- Traffic density simulation
- Strategy optimization
- Virtual Safety Car modelling
- Race pace modelling

### Backend (JS)
- Node.js
- Express
- WebSockets
- Bull Queue
- gRPC (optional)

### Frontend UI
- Next.js
- React
- Tailwind
- Recharts
- Plotly.js
- D3.js
- Framer Motion

### AI / LLM
- GPT / Claude / Gemini
- Prompt engineering layer

### DevOps
- Vercel
- Railway/Render
- GitHub Actions
- AWS S3
- SQLite/PostgreSQL

### Visualization / Fan Mode
- Three.js
- Unity WebGL (optional)
- Spline

---

## 📋 Implementation Status

### ✅ Implemented
- Basic Python ML backend (scikit-learn, SHAP)
- FastAPI service
- Node.js Express API
- Basic Next.js frontend
- Simple Monte Carlo simulation
- Data loading and preprocessing

### 🚧 In Progress / Planned
- [ ] XGBoost/LightGBM integration
- [ ] Sector timing engine
- [ ] Lap classification system
- [ ] Driver behavior metrics
- [ ] Advanced degradation modeling
- [ ] WebSocket real-time updates
- [ ] Bull Queue job management
- [ ] Frontend visualization libraries
- [ ] LLM commentary integration
- [ ] Advanced race simulation features

---

## 📚 References

This stack is inspired by:
- Formula 1 race engineering systems
- WEC (World Endurance Championship) analytics
- IndyCar data platforms
- NASCAR performance systems
- IMSA race timing and strategy tools
- GT3 professional racing software

