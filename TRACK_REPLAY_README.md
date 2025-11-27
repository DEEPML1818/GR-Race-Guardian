# Track Replay & Race Visualization System

## Overview

The **Track Replay Builder** is a comprehensive motorsport data engineering system that converts raw CSV race data into interactive track visualizations with lap-by-lap race progression, overtake detection, and position tracking.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React/Next.js)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Track Select │  │ Race Replay  │  │ Position Map │      │
│  │   Component  │  │  Animation   │  │   Overlay    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ JSON API
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI/Python)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ CSV Parser   │  │ Overtake     │  │ Anomaly      │      │
│  │              │  │ Detector     │  │ Detector     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ CSV Files
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Sources                            │
│  • Race Results CSV (03_Provisional Results_*.CSV)           │
│  • Lap Times CSV (R*_*_lap_time.csv)                        │
│  • Sector Times CSV (optional)                              │
│  • Telemetry CSV (optional)                                 │
└─────────────────────────────────────────────────────────────┘
```

## Features

### 1️⃣ CSV Data Parsing
- **Race Results**: Position, laps, times, gaps
- **Lap Times**: Per-lap timestamps for all drivers
- **Sector Times**: Detailed sector-by-sector analysis
- **Telemetry**: Speed, throttle, brake data (if available)

### 2️⃣ Race Reconstruction
- **Position Calculation**: Determines driver positions for each lap
- **Gap Analysis**: Calculates time gaps to leader and previous driver
- **Lap-by-Lap Timeline**: Complete race progression

### 3️⃣ Event Detection

#### Overtakes
```python
# Detects position changes between laps
"#13 → P1 (+2)"  # Driver 13 moved to P1, gained 2 positions
```

#### Pit Stops
```python
# Identifies slow laps (>150% median)
"#22 Pit Stop"  # Driver 22 pitted on this lap
```

#### Safety Car / Yellow Flags
```python
# Detects when all drivers slow simultaneously
"Safety Car - Lap 15-18"
```

#### DNFs
```python
# Identifies drivers who stopped completing laps
"#88 DNF - Lap 13"
```

### 4️⃣ Track Visualization
- **SVG Track Maps**: Accurate circuit layouts
- **Driver Position Overlay**: Shows car positions on track
- **Animated Replay**: Lap-by-lap race progression
- **Heatmaps**: Traffic density visualization

## API Endpoints

### Build Race Replay
```http
POST /replay/build
Content-Type: application/json

{
  "track_id": "barber",
  "race_id": "R1"
}
```

**Response:**
```json
{
  "success": true,
  "track": "barber",
  "track_name": "Barber Motorsports Park",
  "track_length_miles": 2.38,
  "turns": 17,
  "laps": 27,
  "drivers": ["#13", "#22", "#72", ...],
  "replay": [
    {
      "lap": 1,
      "positions": [
        {
          "driver": "#13",
          "position": 1,
          "gap": 0.0,
          "laps_completed": 1
        },
        ...
      ],
      "events": ["Race Start"]
    },
    ...
  ]
}
```

### Get Available Tracks
```http
GET /replay/tracks
```

**Response:**
```json
{
  "success": true,
  "tracks": [
    {
      "id": "barber",
      "name": "Barber Motorsports Park",
      "races": [
        {"id": "R1", "name": "Race 1"},
        {"id": "R2", "name": "Race 2"}
      ]
    },
    ...
  ]
}
```

## Usage

### Backend

1. **Start the backend server:**
```bash
cd backend-python
python app.py
```

2. **Build a replay programmatically:**
```python
from grracing.race_replay_builder import RaceReplayBuilder

builder = RaceReplayBuilder("barber")
replay_data = builder.build_replay_json(
    results_csv="path/to/results.csv",
    lap_times_csv="path/to/lap_times.csv",
    output_path="barber_race1_replay.json"
)
```

### Frontend

1. **Start the frontend:**
```bash
cd frontend-next
npm run dev
```

2. **Navigate to:**
```
http://localhost:3000/track-replay
```

3. **Select a track and race to view the replay**

## Data Requirements

### Required CSV Files

#### Race Results CSV
```csv
POSITION;NUMBER;STATUS;LAPS;TOTAL_TIME;GAP_FIRST;FL_TIME
1;13;Classified;27;45:15.035;-;1:37.428
2;22;Classified;27;45:17.775;+2.740;1:37.746
...
```

#### Lap Times CSV
```csv
lap,vehicle_number,timestamp,vehicle_id
2,13,2025-09-06T18:40:41.775Z,GR86-002-000
3,13,2025-09-06T18:42:25.504Z,GR86-002-000
...
```

### Optional CSV Files

#### Sector Times
```csv
lap,vehicle_number,sector,time,speed
1,13,1,32.456,145.2
1,13,2,35.123,138.7
...
```

## Track Support

Currently supported tracks:
- ✅ Barber Motorsports Park
- ✅ Circuit of the Americas (COTA)
- ✅ Indianapolis Motor Speedway
- ✅ Road America
- ✅ Sebring International Raceway
- ✅ Sonoma Raceway
- ✅ Virginia International Raceway (VIR)

## Anomaly Detection

### Slow Lap Detection
```python
# Laps >120% of driver's median time
threshold = median_lap_time * 1.2
```

### Pit Stop Detection
```python
# Laps >150% of driver's median time
pit_threshold = median_lap_time * 1.5
```

### Safety Car Detection
```python
# When >50% of field slows simultaneously
if slow_drivers / total_drivers > 0.5:
    safety_car_lap = True
```

## Future Enhancements

- [ ] Real-time WebSocket streaming
- [ ] 3D track visualization
- [ ] Telemetry overlay (speed, throttle, brake)
- [ ] Sector-by-sector comparison
- [ ] Driver onboard camera sync
- [ ] Race strategy analysis
- [ ] Tire compound tracking
- [ ] Weather data integration
- [ ] Predictive overtake probability
- [ ] Export to video/GIF

## Troubleshooting

### "CSV files not found"
- Ensure CSV files are in the correct track directory
- Check file naming conventions match expected patterns

### "No replay data"
- Verify CSV files contain valid data
- Check that lap times have timestamps
- Ensure vehicle numbers match between files

### "Overtakes not detected"
- Verify lap times are chronologically ordered
- Check for duplicate lap entries
- Ensure position data is consistent

## Contributing

This system is designed to be extensible. To add support for new tracks:

1. Add track info to `_get_track_info()` in `race_replay_builder.py`
2. Add track coordinates to `track_coordinates.py`
3. Place CSV files in `{track-name}/{track-name}/` directory

## License

Part of GR Race Guardian - Professional Motorsport Analytics Platform
