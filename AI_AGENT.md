# 🤖 GR-RACE-GUARDIAN-AI Agent

## Overview

GR-RACE-GUARDIAN-AI is the central intelligence agent of the GR Race Guardian platform. It operates as a unified race engineer, data analyst, strategy director, and driver coach.

## Features

The AI agent analyzes motorsport data and provides insights in **7 different modes**:

1. **Engineering** - Professional race engineer output
2. **Strategy** - Real-time tactical decisions
3. **Coach** - Driver improvement analysis
4. **Fan** - Storytelling and excitement
5. **Summary** - Race recap
6. **Compare** - Side-by-side driver comparison
7. **Pit Decision** - Should we pit now?

## API Endpoints

### Main Analysis Endpoint
```
POST /api/ai/analyze
```

**Request Body:**
```json
{
  "mode": "engineering",
  "driver_twin": {
    "pace_vector": 0.05,
    "consistency_index": 0.92,
    "aggression_score": 0.65,
    "sector_strengths": {
      "S1": 0.95,
      "S2": 0.88,
      "S3": 0.91
    }
  },
  "race_twin": {
    "expected_finishing_positions": [{"position": 1}],
    "pit_recommendations": "Pit window: laps 18-22",
    "tire_cliff_prediction": {"lap": 25}
  },
  "lap_data": [
    {"lap": 1, "lap_time": 95.234, "sector": "S1"}
  ],
  "events": [
    {"type": "pit_stop", "lap": 20}
  ],
  "weather": {
    "temperature": 28,
    "condition": "dry"
  }
}
```

### Mode-Specific Endpoints

- `POST /api/ai/engineering` - Engineering mode analysis
- `POST /api/ai/strategy` - Strategy mode analysis
- `POST /api/ai/coach` - Coach mode analysis
- `POST /api/ai/fan` - Fan mode analysis
- `POST /api/ai/pit-decision` - Pit decision analysis

## Modes Explained

### 1. Engineering Mode
**Output Structure:**
- Executive Summary
- Key Insights
- Driver Twin Interpretation
- Race Twin Interpretation
- Tire & Pace Analysis
- Strategy Recommendation
- Sector Breakdown
- Risk Factors & Confidence
- Action Items

**Example Output:**
```json
{
  "mode": "engineering",
  "sections": {
    "executive_summary": "Expected finishing position: P1. Consistency index: 92.0%. Average lap time: 95.234s",
    "key_insights": [
      "Pace vector: 0.050 - strong performance",
      "Tire cliff predicted at lap 25"
    ],
    "driver_twin_interpretation": {
      "pace_analysis": "Pace vector: 0.050",
      "consistency_analysis": "Consistency: 92.0% (good)"
    },
    "strategy_recommendation": [
      "Pit window: laps 18-22",
      "Monitor tire degradation - cliff predicted around lap 25"
    ]
  }
}
```

### 2. Strategy Mode
**Output:**
- Recommendation
- Reasoning
- Confidence level
- Traffic impact analysis
- Undercut analysis

### 3. Coach Mode
**Output:**
- Driver strengths
- Driver weaknesses
- Consistency analysis
- Actionable improvements

### 4. Fan Mode
**Output:**
- Headline
- Race story
- Top moments
- Driver highlights
- Final wrap-up

### 5. Pit Decision Mode
**Output:**
- Decision: `PIT_NOW`, `PIT_LATER`, or `EXTEND_STINT`
- Confidence: `high`, `medium`, or `low`
- Reasoning array
- Factors evaluated:
  - Degradation
  - Traffic window
  - Tire age
  - Undercut viability

## Usage Examples

### Example 1: Engineering Analysis

```javascript
const response = await fetch('http://localhost:3001/api/ai/engineering', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    driver_twin: {
      consistency_index: 0.92,
      aggression_score: 0.65,
      sector_strengths: { S1: 0.95, S2: 0.88, S3: 0.91 }
    },
    race_twin: {
      pit_recommendations: "Pit window: laps 18-22",
      tire_cliff_prediction: { lap: 25 }
    },
    lap_data: [
      { lap: 1, lap_time: 95.234 },
      { lap: 2, lap_time: 95.456 }
    ]
  })
});

const analysis = await response.json();
console.log(analysis.analysis.sections);
```

### Example 2: Pit Decision

```javascript
const response = await fetch('http://localhost:3001/api/ai/pit-decision', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    race_twin: {
      degradation_curve: { critical: false, trend: 'increasing' },
      traffic_simulation: { clear_window: true },
      tire_age: 15,
      undercut_outcomes: { viable: true, time_gain: 2.5 }
    }
  })
});

const decision = await response.json();
console.log(`Decision: ${decision.analysis.decision}`);
console.log(`Reasoning: ${decision.analysis.reasoning.join(', ')}`);
```

### Example 3: Compare Two Drivers

```javascript
const response = await fetch('http://localhost:3001/api/ai/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    mode: 'compare',
    compare_drivers: [
      {
        id: 'driver_1',
        consistency_index: 0.92,
        aggression_score: 0.65,
        pace_vector: 0.05
      },
      {
        id: 'driver_2',
        consistency_index: 0.88,
        aggression_score: 0.72,
        pace_vector: 0.03
      }
    ]
  })
});

const comparison = await response.json();
console.log(comparison.analysis.comparison);
```

## Data Input Format

### Driver Twin JSON
```json
{
  "pace_vector": 0.05,
  "consistency_index": 0.92,
  "aggression_score": 0.65,
  "degradation_curve": {...},
  "sector_strengths": {
    "S1": 0.95,
    "S2": 0.88,
    "S3": 0.91
  }
}
```

### Race Twin JSON
```json
{
  "expected_finishing_positions": [{"position": 1}],
  "pit_recommendations": "Pit window: laps 18-22",
  "undercut_outcomes": {
    "viable": true,
    "time_gain": 2.5
  },
  "tire_cliff_prediction": {
    "lap": 25
  },
  "traffic_simulation": {
    "clear_window": true,
    "busy": false
  },
  "monte_carlo_outcomes": {...}
}
```

### Lap Data JSON
```json
[
  {
    "lap": 1,
    "lap_time": 95.234,
    "sector": "S1",
    "delta_to_best": 0.5,
    "delta_to_leader": 0.0
  }
]
```

### Events JSON
```json
[
  {"type": "overtake", "lap": 15},
  {"type": "pit_stop", "lap": 20},
  {"type": "safety_car", "lap": 25}
]
```

## Behavior Rules

✅ **MUST:**
- Only analyze EXACTLY what is provided
- Use professional motorsport terminology
- Provide actionable, data-driven insights
- Speak like a real race engineer
- Cite real data from inputs
- Never hallucinate unknown data

❌ **MUST NOT:**
- Invent or hallucinate data
- Use vague language
- Apologize or show uncertainty (except in confidence intervals)
- Reference self as an AI model
- Behave like a chatbot

## Implementation

The AI agent is implemented in:
- **Service**: `backend-node/services/race-engineer-ai.js`
- **Routes**: `backend-node/routes/ai-route.js`
- **Integration**: `backend-node/server.js` (routes mounted at `/api/ai`)

## Testing

Test the AI agent:

```bash
# Start the server
cd backend-node
node server.js

# Test engineering mode
curl -X POST http://localhost:3001/api/ai/engineering \
  -H "Content-Type: application/json" \
  -d '{
    "driver_twin": {
      "consistency_index": 0.92,
      "aggression_score": 0.65
    }
  }'
```

## Integration with Frontend

The AI agent can be integrated into the frontend dashboard to provide real-time race engineering insights alongside the live race data.

---

**The AI agent is ready to analyze your race data! 🏎️🤖**

