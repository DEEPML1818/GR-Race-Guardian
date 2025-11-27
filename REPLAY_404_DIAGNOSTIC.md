# Replay Endpoint 404 Error - Diagnostic Guide

## Current Status

### ✅ Backend Tests PASS
- Endpoint `/replay/build` exists and is registered
- Python test successfully retrieves replay data
- Server is running on port 8000 (PID 18960)
- CORS is configured to allow all origins
- Numpy serialization fix is working

### ❌ Frontend Gets 404
- Browser shows: `POST http://localhost:8000/replay/build 404 (Not Found)`
- Error occurs in `track-replay.js:50`

## Possible Causes

### 1. Server Not Fully Restarted
**Symptom**: Old server instance still running
**Solution**:
```bash
# Find and kill the Python process
tasklist | findstr python
taskkill /F /PID 18960

# Restart the server
cd backend-python
python app.py
```

### 2. Browser Cache Issue
**Symptom**: Browser cached old API responses
**Solution**:
- Open browser DevTools (F12)
- Go to Network tab
- Check "Disable cache"
- Hard refresh (Ctrl+Shift+R)

### 3. Next.js Dev Server Not Running
**Symptom**: Frontend not accessible
**Solution**:
```bash
cd frontend-next
npm run dev
```

### 4. Request Timing Issue
**Symptom**: Frontend loads before backend is ready
**Solution**: Wait a few seconds after starting backend before accessing frontend

## Diagnostic Steps

### Step 1: Verify Backend is Running
```bash
cd backend-python
python test_server_endpoints.py
```
Expected output: `[EXISTS] POST /replay/build (status: 422)`

### Step 2: Test from Browser
1. Open `test_replay_browser.html` in your browser
2. Click "Test /replay/build Endpoint"
3. Should show SUCCESS with replay data

### Step 3: Check Frontend Request
1. Open browser DevTools (F12)
2. Go to Network tab
3. Navigate to track replay page
4. Select a track and race
5. Look for the `/replay/build` request
6. Check:
   - Request URL (should be `http://localhost:8000/replay/build`)
   - Request Method (should be POST)
   - Request Payload (should have `track_id` and `race_id`)
   - Response status

### Step 4: Check Console for Errors
Look for:
- CORS errors
- Network errors
- JavaScript errors

## Quick Fix Checklist

- [ ] Backend server is running (`python app.py`)
- [ ] Frontend server is running (`npm run dev`)
- [ ] Backend shows no errors in console
- [ ] Browser cache is disabled
- [ ] Hard refresh the frontend page
- [ ] Check Network tab for actual request details

## If Still Not Working

### Check if Multiple Servers are Running
```bash
netstat -ano | findstr :8000
```
Should show only ONE process on port 8000

### Check Backend Logs
Look at the terminal running `python app.py` for:
- Request logs when you click the button
- Error messages
- Stack traces

### Verify Endpoint Registration
```bash
# Visit FastAPI auto-generated docs
http://localhost:8000/docs
```
Look for `/replay/build` in the endpoint list

## Expected Behavior

When working correctly:
1. User selects track "Barber"
2. User selects race "Race 1"
3. Frontend sends: `POST http://localhost:8000/replay/build`
   ```json
   {
     "track_id": "barber",
     "race_id": "race-1"
   }
   ```
4. Backend responds with status 200:
   ```json
   {
     "success": true,
     "track": "barber",
     "track_name": "Barber Motorsports Park",
     "laps": 28,
     "drivers": [...],
     "replay": [...]
   }
   ```
5. Frontend displays track map and replay controls

## Contact Points

If the issue persists, provide:
1. Screenshot of browser Network tab showing the failed request
2. Backend console output
3. Frontend console errors
4. Output of `test_server_endpoints.py`
