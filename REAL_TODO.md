# 🔥 GR Race Guardian - Real Development TODO

**Status**: Core features need implementation  
**Priority**: Engineering tasks for production-ready system

---

## 🧠 1. Digital Driver Twin

### Status: ⚠️ **THEORY EXISTS, IMPLEMENTATION MISSING**

**Files to Create/Update:**
- [ ] `backend-python/grracing/driver_twin.py` - Complete Driver Twin generator
- [ ] `backend-python/grracing/driver_twin_loop.py` - Update loop for real-time recalculation

**Required Formulas:**

#### Pace Vector
- [ ] Calculate from recent lap times vs best lap time
- [ ] Formula: `pace_vector = (avg_lap_time - best_lap_time) / best_lap_time`
- [ ] Normalize to -0.1 to +0.1 range

#### Consistency Index
- [ ] Calculate standard deviation of lap times
- [ ] Formula: `consistency = 1 - (std_dev / mean_lap_time)`
- [ ] Normalize to 0.0 to 1.0 (1.0 = perfect consistency)

#### Aggression Score
- [ ] Analyze throttle/brake patterns
- [ ] Cornering speeds vs optimal
- [ ] Overtake attempts frequency
- [ ] Formula: `aggression = (throttle_variance + brake_aggressiveness + corner_speed_ratio) / 3`

#### Tire Degradation Profile
- [ ] Track pace drop-off per lap
- [ ] Fit exponential curve: `pace = base_pace * (1 + degradation_rate * lap_number)`
- [ ] Store degradation_rate coefficient

#### Sector Strength Vector
- [ ] Calculate relative performance in S1, S2, S3
- [ ] Formula: `sector_strength[i] = (driver_sector[i] - avg_sector[i]) / avg_sector[i]`
- [ ] Output: `{"S1": 0.95, "S2": 0.88, "S3": 0.91}`

#### Fatigue/Long-Run Dropoff Model
- [ ] Track pace degradation over long stints
- [ ] Formula: `fatigue_factor = fatigue_base * (1 - exp(-lap_number / fatigue_constant))`
- [ ] Predict performance drop after X laps

#### Output JSON Generator
- [ ] Create standardized Driver Twin JSON:
```json
{
  "driver_id": "driver_1",
  "pace_vector": 0.05,
  "consistency_index": 0.92,
  "aggression_score": 0.65,
  "degradation_profile": {
    "rate": 0.0023,
    "type": "exponential",
    "compound": "MEDIUM"
  },
  "sector_strengths": {
    "S1": 0.95,
    "S2": 0.88,
    "S3": 0.91
  },
  "fatigue_dropoff": {
    "factor": 0.02,
    "critical_lap": 25
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "lap_count": 15
}
```

#### Driver Twin Update Loop
- [ ] Recalculate every lap
- [ ] Emit to Node.js via API or WebSocket
- [ ] Cache previous values for comparison

---

## 🏁 2. Digital Race Twin Simulator

### Status: ⚠️ **PROTOTYPE EXISTS, CORE LOGIC MISSING**

**Files to Create/Update:**
- [ ] `backend-python/grracing/race_twin.py` - Complete Monte Carlo engine
- [ ] `backend-python/grracing/pit_rejoin.py` - Pit rejoin simulator
- [ ] `backend-python/grracing/strategy_optimizer.py` - Strategy optimization

**Required Features:**

#### Monte Carlo Race Simulation Engine
- [ ] Simulate 100-500 race outcomes
- [ ] For each simulation:
  - [ ] Lap-by-lap pace progression
  - [ ] Tire degradation modeling
  - [ ] Overtake probability application
  - [ ] Pit stop timing and duration
  - [ ] Traffic impact on pace
  - [ ] Weather effects (if applicable)
- [ ] Return win/position probabilities:
```json
{
  "expected_finishing_positions": [
    {"position": 1, "probability": 0.45},
    {"position": 2, "probability": 0.35},
    {"position": 3, "probability": 0.20}
  ],
  "confidence_intervals": {...}
}
```

#### Pit Rejoin Simulator
- [ ] Predict rejoin position after pit stop
- [ ] Calculate time lost in traffic
- [ ] Ghost driver simulation (where would we be without pit?)
- [ ] Formula: `rejoin_position = current_position + cars_passed_during_pit`
- [ ] Traffic impact: `time_lost = traffic_density * sector_length * speed_delta`

#### Strategy Optimizer
- [ ] Best lap to pit calculator
- [ ] Undercut vs overcut modeling
  - [ ] Undercut: Pit early, gain on fresh tires
  - [ ] Overcut: Stay out longer, benefit from tire degradation
- [ ] Degradation-aware decision engine
- [ ] Formula: `optimal_pit_lap = f(degradation_rate, traffic_window, tire_age)`

#### RaceTwin JSON Output Builder
- [ ] Standardized output format:
```json
{
  "race_id": "race_1",
  "simulations": 500,
  "expected_finishing_positions": [...],
  "pit_recommendations": {
    "optimal_window": {"start": 18, "end": 22},
    "undercut_viable": true,
    "time_gain": 2.5
  },
  "tire_cliff_prediction": {
    "lap": 25,
    "critical": true
  },
  "traffic_simulation": {
    "clear_window": true,
    "busy": false
  },
  "monte_carlo_outcomes": {...}
}
```

---

## 🔮 3. ML Models

### Status: ⚠️ **PROTOTYPES EXIST, PRODUCTION MODELS MISSING**

**Files to Create/Update:**
- [ ] `backend-python/grracing/models/lap_time_predictor.py` - Full lap time prediction
- [ ] `backend-python/grracing/models/tire_degradation.py` - Production degradation model
- [ ] `backend-python/grracing/models/traffic_loss.py` - Traffic loss model

**Required Models:**

#### Lap Time Prediction Model
- [ ] Features:
  - [ ] Temperature (track and ambient)
  - [ ] Tire age (laps on tires)
  - [ ] Stint number
  - [ ] Fuel load
  - [ ] Track condition
  - [ ] Sector times
- [ ] Train XGBoost model
- [ ] Save model with joblib
- [ ] API endpoint: `POST /predict/lap`

#### Tire Degradation Model
- [ ] Fit exponential or polynomial curves to data
- [ ] Detect tire cliff (sudden drop-off)
- [ ] Predict drop-off rate
- [ ] Compound-specific coefficients
- [ ] Formula: `degradation = base * (1 + rate * age^exponent)`
- [ ] API endpoint: `POST /predict/degradation`

#### Traffic Loss Model
- [ ] Calculate clean air delta
- [ ] Traffic penalty per car ahead
- [ ] Sector-based traffic cost
- [ ] Formula: `time_lost = base_penalty + (cars_ahead * penalty_per_car) + (sector_traffic_density * sector_multiplier)`
- [ ] API endpoint: `POST /predict/traffic-loss`

---

## 🛰 4. Backend API Layer

### Status: ⚠️ **PARTIAL, NEEDS UNIFICATION**

**Files to Create/Update:**
- [ ] `backend-python/app.py` - Add new endpoints
- [ ] `backend-node/services/data-bridge.js` - Unified data bridge
- [ ] `backend-node/services/live-data-packet.js` - Combined data packet generator

**Required Endpoints:**

#### Python API Endpoints
- [ ] `GET /driver-twin/:driver_id` - Get current Driver Twin
- [ ] `POST /driver-twin/update` - Update Driver Twin with new lap data
- [ ] `POST /race-twin/simulate` - Run Monte Carlo simulation
- [ ] `GET /race-twin/:race_id` - Get current Race Twin
- [ ] `POST /predict/lap` - Predict future lap time
- [ ] `POST /predict/stint` - Predict stint pace
- [ ] `POST /strategy/pit-decision` - Get pit decision recommendation

#### Node.js Bridge
- [ ] Fetch Python results
- [ ] Cache results (Redis or in-memory)
- [ ] Send to frontend via WebSocket
- [ ] Handle failures gracefully

#### Combined Live Data Packet
- [ ] Single data packet every second:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "lap": 15,
  "liveData": {
    "lap_times": [...],
    "positions": [...],
    "sectors": [...]
  },
  "driverTwin": {
    "driver_1": {...},
    "driver_2": {...}
  },
  "raceTwin": {
    "expected_positions": [...],
    "pit_recommendations": {...}
  },
  "predictions": {
    "next_lap_time": 95.234,
    "tire_degradation": 0.02
  },
  "strategy": {
    "pit_decision": "PIT_LATER",
    "optimal_window": {...}
  }
}
```

---

## 🎨 5. Frontend Elements

### Status: ⚠️ **BASIC VERSIONS EXIST, FEATURES MISSING**

**Files to Update:**
- [ ] `frontend-next/components/race/TrafficMap.jsx` - Add track visual, ghost path
- [ ] `frontend-next/components/race/StrategyConsole.jsx` - Add degradation graph, undercut/overcut
- [ ] `frontend-next/components/race/PitDecisionPanel.jsx` - Add confidence bar, explanation popout
- [ ] `frontend-next/components/race/AIAgentPanel.jsx` - Create new component
- [ ] `frontend-next/components/race/MultiDriverComparison.jsx` - Add radar chart, Twin comparison

**Required Features:**

#### Traffic Rejoin Map
- [ ] Track visual (SVG or Canvas)
- [ ] Driver markers with positions
- [ ] Traffic density heatmap overlay
- [ ] Pit rejoin ghost path visualization
- [ ] Animated traffic flow

#### Strategy Console
- [ ] Visual pit windows (timeline)
- [ ] Tire degradation graph over race
- [ ] Undercut/overcut simulator (visual comparison)
- [ ] Risk scoring display
- [ ] Stint-by-stint breakdown

#### Pit Decision Panel
- [ ] AI decision display (prominent)
- [ ] Confidence bar (visual indicator)
- [ ] Explanation popout (detailed reasoning)
- [ ] Factor breakdown (degradation, traffic, etc.)
- [ ] Historical decision tracking

#### AI Agent Panel (NEW)
- [ ] Chat window interface
- [ ] Mode selector (7 modes)
- [ ] Auto-insert data button (inject current race state)
- [ ] Inspector for last lap data
- [ ] Response formatting

#### Comparison Dashboard
- [ ] Radar chart (sector + skill metrics)
- [ ] Lap-by-lap delta graph
- [ ] Twin vs Twin comparison (Driver Twin vectors)
- [ ] Consistency overlay
- [ ] Pace vector visualization

---

## 🤖 6. AI Agent System

### Status: ⚠️ **CORE EXISTS, TOOL-CALLING MISSING**

**Files to Create/Update:**
- [ ] `backend-node/services/race-engineer-ai.js` - Add tool-calling
- [ ] `backend-node/services/ai-tools.js` - Tool implementations
- [ ] `backend-node/services/ai-templates.js` - Response templates

**Required Features:**

#### Response Templates for Each Mode
- [ ] Engineering template
- [ ] Strategy template
- [ ] Coach template
- [ ] Fan template
- [ ] Summary template
- [ ] Compare template
- [ ] Pit decision template

#### Tool-Calling Functions
- [ ] `getDriverTwin(driverId)` - Fetch Driver Twin data
- [ ] `getRaceTwin(raceId)` - Fetch Race Twin data
- [ ] `getPitDecision(raceId, driverId)` - Get pit recommendation
- [ ] `runMonteCarlo(params)` - Run simulation on demand
- [ ] `evaluateSectors(driverId)` - Analyze sector performance

#### Fallback Logic
- [ ] If missing data → respond gracefully
- [ ] If model fails → use defaults
- [ ] If API error → cached response
- [ ] Error messages in user-friendly format

---

## ⚙️ 7. Core Foundation & Stability

### Status: ⚠️ **BASIC, NEEDS ENHANCEMENT**

**Files to Create/Update:**
- [ ] `backend-python/utils/logging_config.py` - Python logging
- [ ] `backend-node/utils/logger.js` - Node logging
- [ ] `backend-python/utils/error_handler.py` - Error handling
- [ ] `backend-node/utils/error_handler.js` - Error handling
- [ ] `start_all.bat` / `start_all.ps1` - Enhanced startup

**Required Features:**

#### Logging System
- [ ] Python logging (file + console)
- [ ] Node logging (file + console)
- [ ] Unified error logs
- [ ] Log rotation
- [ ] Log levels (DEBUG, INFO, WARNING, ERROR)

#### Fallback and Recovery
- [ ] If Python crashes → retry (3 attempts)
- [ ] If model fails → default values
- [ ] If WebSocket drops → auto reconnect
- [ ] Circuit breaker pattern
- [ ] Health check monitoring

#### Enhanced Startup Scripts
- [ ] Check dependencies (Node, Python, npm, pip)
- [ ] Restart Python if crash detected
- [ ] Delay logic for dependencies (wait for Python before starting Node)
- [ ] Status monitoring
- [ ] Graceful shutdown

---

## 📊 Implementation Priority

### High Priority (Week 1)
1. ✅ Digital Driver Twin (complete implementation)
2. ✅ Digital Race Twin (Monte Carlo engine)
3. ✅ Unified Live Data Packet
4. ✅ Enhanced ML Models

### Medium Priority (Week 2)
5. ✅ Frontend enhancements (missing features)
6. ✅ AI Agent tool-calling
7. ✅ Logging system

### Low Priority (Week 3)
8. ✅ Error handling improvements
9. ✅ Enhanced startup scripts
10. ✅ Polish and optimization

---

**Status**: Ready to implement  
**Next Step**: Start with Digital Driver Twin implementation

