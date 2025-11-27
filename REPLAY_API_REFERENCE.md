# Track Replay API - Quick Reference

## ✅ Endpoint is Working!

The `/replay/build` endpoint is now active and functional.

## 🔄 **IMPORTANT: Restart Required**

After updating `app.py`, you MUST restart the backend server:

```bash
# In your backend terminal:
# 1. Press CTRL+C to stop
# 2. Run: python app.py
```

## 📝 Correct Race ID Formats

Use these race IDs when calling the API:

| Track | Race ID Options |
|-------|----------------|
| Barber | `race-1` or `race-2` |
| COTA | `race-1` or `race-2` |
| Indianapolis | `race-1` or `race-2` |
| Road America | `race-1` or `race-2` |
| Sebring | `race-1` or `race-2` |
| Sonoma | `race-1` or `race-2` |
| VIR | `race-1` or `race-2` |

## 🧪 Test the Endpoint

### Using curl:
```bash
curl -X POST http://localhost:8000/replay/build \
  -H "Content-Type: application/json" \
  -d "{\"track_id\": \"barber\", \"race_id\": \"race-1\"}"
```

### Using the test script:
```bash
cd backend-python
python test_endpoints.py
```

### Using the frontend:
```
http://localhost:3000/track-replay
```

## 🐛 Troubleshooting

### "404 Not Found" Error
- ✅ Endpoint is registered correctly
- ❌ Server needs restart
- **Solution**: Restart the backend server (CTRL+C then `python app.py`)

### "CSV files not found" Error
- Check the race_id format (use `race-1` not `R1`)
- The error message now shows how many CSV files were found
- Verify CSV files exist in the track directory

### Files Not Found
The endpoint now searches recursively and will tell you:
- How many results files it found
- How many lap time files it found
- The directory it searched in

## ✨ What Changed

**Before:**
- Only searched in immediate directory
- Required exact race ID match
- Generic error messages

**After:**
- Searches recursively in subdirectories
- Handles multiple race ID formats (`race-1`, `R1`, `1`)
- Provides detailed error messages with file counts
- Shows the search directory for debugging

## 🚀 Ready to Use!

Once you restart the server, the Track Replay system is fully operational!
