# 🗺️ Track Visualization & Race Replay System

## ✅ Implementation Complete

A comprehensive track map visualization and race replay system for all 7 race tracks.

---

## 🏁 Supported Tracks

1. **Barber Motorsports Park** - 2.38 miles, 17 turns
2. **Circuit of the Americas (COTA)** - 3.427 miles, 20 turns
3. **Indianapolis Motor Speedway** - 2.439 miles, 14 turns
4. **Road America** - 4.048 miles, 14 turns
5. **Sebring International Raceway** - 3.74 miles, 17 turns
6. **Sonoma Raceway** - 2.52 miles, 12 turns
7. **Virginia International Raceway (VIR)** - 3.27 miles, 17 turns

---

## 📁 Files Created

### Backend (Python)

1. **`backend-python/grracing/track_data_parser.py`**
   - Parses CSV files from track folders
   - Extracts race results, lap times, and replay data
   - Supports all 7 tracks with Race 1/Race 2

2. **`backend-python/grracing/track_coordinates.py`**
   - Defines coordinate systems for all tracks
   - Generates SVG paths for visualization
   - Normalized coordinates (0-1) for rendering

### Frontend (Next.js)

3. **`frontend-next/pages/tracks.js`**
   - Main page for track visualization
   - Track and race selection
   - Data fetching and state management

4. **`frontend-next/components/tracks/TrackMapView.jsx`**
   - SVG track visualization
   - Driver positions on track
   - Race results table
   - Interactive driver selection

5. **`frontend-next/components/tracks/RaceReplay.jsx`**
   - Race replay controls (Play/Pause/Reset)
   - Lap-by-lap progression
   - Position changes visualization
   - Playback speed control (0.5x, 1x, 2x, 5x)

### API Endpoints

6. **Python FastAPI Endpoints:**
   - `GET /tracks/available` - List all available tracks
   - `POST /tracks/results` - Get race results
   - `POST /tracks/lap-times` - Get lap times
   - `POST /tracks/replay` - Get complete replay data
   - `GET /tracks/{track_id}/coordinates` - Get track coordinates

---

## 🎯 Features

### 1. Track Map Visualization
- **SVG-based track layout** for each track
- **Start/Finish line** marked in red
- **Driver positions** shown as colored circles
- **Position indicators** (P1, P2, P3, etc.)
- **Interactive selection** - click drivers to highlight

### 2. Race Replay System
- **Play/Pause controls** for replay
- **Lap slider** to jump to any lap
- **Playback speed** control (0.5x to 5x)
- **Lap-by-lap positions** table
- **Race summary** with winner and statistics

### 3. Race Results Display
- **Complete results table** with:
  - Position (with podium colors)
  - Vehicle number
  - Total laps
  - Total time
  - Gap to first
- **Interactive selection** - click rows to highlight on map

### 4. Track Information
- **Track name** and details
- **Track length** in miles
- **Number of turns**
- **Track layout** visualization

---

## 🚀 How to Use

### Access the Page

1. **Start the application:**
   ```bash
   # Run start_all.bat or start services manually
   ```

2. **Navigate to tracks page:**
   - Click "🗺️ View Race Tracks" button on main page
   - Or go directly to: `http://localhost:3000/tracks`

### Using the Interface

1. **Select Track:**
   - Choose from dropdown (Barber, COTA, Indianapolis, etc.)

2. **Select Race:**
   - Choose Race 1 or Race 2 for the selected track

3. **View Track Map:**
   - See track layout with driver positions
   - Click drivers to highlight them
   - View race results table

4. **Watch Race Replay:**
   - Click "▶ Play" to start replay
   - Use slider to jump to specific laps
   - Adjust playback speed
   - See position changes lap-by-lap

---

## 📊 Data Structure

### Track Data Files
Each track folder contains:
- `*_lap_time.csv` - Lap timing data
- `*_lap_start.csv` - Lap start times
- `*_lap_end.csv` - Lap end times
- `*_telemetry_data.csv` - Telemetry data
- `*_Results*.CSV` - Race results

### API Response Format

**Race Results:**
```json
{
  "success": true,
  "track_id": "barber",
  "race_id": "race-1",
  "results": [
    {
      "position": 1,
      "vehicle_number": "13",
      "total_time": "45:15.035",
      "gap_first": "-",
      "laps": 27,
      "status": "Classified"
    }
  ],
  "total_drivers": 20
}
```

**Race Replay:**
```json
{
  "success": true,
  "track_id": "barber",
  "race_id": "race-1",
  "results": [...],
  "lap_progression": [
    {
      "lap": 1,
      "positions": [
        {
          "vehicle_id": "GR86-001-000",
          "vehicle_number": "13",
          "lap": 1,
          "position": 1
        }
      ]
    }
  ]
}
```

**Track Coordinates:**
```json
{
  "success": true,
  "track_id": "barber",
  "track_info": {
    "name": "Barber Motorsports Park",
    "length": 2.38,
    "turns": 17
  },
  "coordinates": [
    {
      "x": 0.1,
      "y": 0.5,
      "type": "start_finish",
      "name": "Start/Finish"
    }
  ],
  "svg_path": "M 100 500 Q ... Z"
}
```

---

## 🎨 Visual Features

### Track Map
- **Track outline** in dark gray
- **Center line** in white (dashed)
- **Start/Finish line** in red
- **Driver markers:**
  - Gold for P1
  - Silver for P2
  - Bronze for P3
  - Green for others

### Race Replay
- **Podium highlighting** in results table
- **Current lap indicator**
- **Position changes** shown in real-time
- **Smooth playback** with adjustable speed

---

## 🔧 Technical Details

### Track Coordinate System
- **Normalized coordinates** (0-1) for universal rendering
- **SVG path generation** for smooth track curves
- **Scalable** to any screen size

### Data Parsing
- **CSV parsing** with multiple delimiter support (`,` and `;`)
- **Error handling** for missing files
- **Race detection** (Race 1, Race 2, or direct files)

### Performance
- **Efficient rendering** with SVG
- **Lazy loading** of race data
- **Optimized** for large datasets

---

## 🎯 Future Enhancements

Potential improvements:
- [ ] More accurate track layouts from PDF maps
- [ ] Real-time position interpolation
- [ ] Sector timing visualization
- [ ] Overtake detection and highlighting
- [ ] Pit stop indicators
- [ ] Telemetry overlay
- [ ] Export race replay as video

---

## 📝 Notes

- **Separate Page**: This feature is completely separate from the main dashboard
- **Data Source**: Reads from CSV files in track folders
- **Track Layouts**: Currently uses generic layouts - can be enhanced with actual track PDF data
- **Race Progression**: Simplified position calculation - can be enhanced with full timing data

---

## ✅ Status: COMPLETE

All features are implemented and ready to use. The track visualization and race replay system is fully functional for all 7 tracks.

**Access at:** `http://localhost:3000/tracks` 🏁

