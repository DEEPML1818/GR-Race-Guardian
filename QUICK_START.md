# ⚡ Quick Start — Your First Feature Implementation

This guide helps you implement your **first feature** step-by-step. We recommend starting with **Real-Time WebSocket Updates** as it provides immediate visible impact.

---

## 🎯 Step 1: Real-Time WebSocket Updates (Recommended First Feature)

### Why Start Here?
- ✅ Immediate visible impact
- ✅ Makes the system feel "alive"
- ✅ Relatively straightforward
- ✅ Dependencies already installed

### Time Required: 4-6 hours

---

## 🚀 Implementation Steps

### Step 1.1: Update Backend Node.js Server

**File**: `backend-node/server.js`

**Action**: Update to include WebSocket support

```javascript
const express = require('express');
const { createServer } = require('http');
const { Server } = require('socket.io');
const bodyParser = require('body-parser');
const { spawn } = require('child_process');
const path = require('path');

const app = express();
const httpServer = createServer(app);
const io = new Server(httpServer, {
  cors: {
    origin: "http://localhost:3000",
    methods: ["GET", "POST"]
  }
});

app.use(bodyParser.json());

// Existing API endpoint
app.post('/api/predict', (req, res) => {
  // ... existing code ...
});

// WebSocket connection handler
io.on('connection', (socket) => {
  console.log('Client connected:', socket.id);
  
  // Subscribe to race updates
  socket.on('subscribe-race', (raceId) => {
    socket.join(`race-${raceId}`);
    console.log(`Client ${socket.id} subscribed to race ${raceId}`);
  });
  
  // Unsubscribe
  socket.on('unsubscribe-race', (raceId) => {
    socket.leave(`race-${raceId}`);
  });
  
  // Disconnect handler
  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id);
  });
});

// Function to broadcast race updates
function broadcastRaceUpdate(raceId, update) {
  io.to(`race-${raceId}`).emit('race-update', update);
}

// Example: Simulate race updates (replace with real data source)
setInterval(() => {
  broadcastRaceUpdate(1, {
    timestamp: new Date().toISOString(),
    drivers: [
      { id: 'driver_1', lap: 10, lapTime: 95.234, position: 1, sector: 'S2' },
      { id: 'driver_2', lap: 10, lapTime: 95.567, position: 2, sector: 'S2' }
    ]
  });
}, 1000); // Update every second

const PORT = process.env.PORT || 3001;
httpServer.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
  console.log(`WebSocket server ready`);
});
```

**Next Steps**:
1. Save this file
2. Restart your Node.js server: `cd backend-node && node server.js`
3. You should see "WebSocket server ready" in console

---

### Step 1.2: Create Frontend WebSocket Hook

**File**: `frontend-next/hooks/useSocket.js` (create this file)

```javascript
import { useEffect, useState, useRef } from 'react';
import { io } from 'socket.io-client';

export function useSocket(raceId) {
  const [isConnected, setIsConnected] = useState(false);
  const [updates, setUpdates] = useState([]);
  const socketRef = useRef(null);
  
  useEffect(() => {
    // Connect to WebSocket server
    const socket = io('http://localhost:3001', {
      transports: ['websocket']
    });
    
    socketRef.current = socket;
    
    // Connection handlers
    socket.on('connect', () => {
      console.log('Connected to WebSocket server');
      setIsConnected(true);
      
      // Subscribe to race updates
      if (raceId) {
        socket.emit('subscribe-race', raceId);
      }
    });
    
    socket.on('disconnect', () => {
      console.log('Disconnected from WebSocket server');
      setIsConnected(false);
    });
    
    // Listen for race updates
    socket.on('race-update', (data) => {
      console.log('Race update received:', data);
      setUpdates(prev => [...prev, data].slice(-50)); // Keep last 50 updates
    });
    
    // Cleanup on unmount
    return () => {
      if (socket) {
        socket.emit('unsubscribe-race', raceId);
        socket.disconnect();
      }
    };
  }, [raceId]);
  
  return {
    isConnected,
    updates,
    socket: socketRef.current
  };
}
```

**Next Steps**:
1. Create `frontend-next/hooks/` directory if it doesn't exist
2. Save this file
3. Create `frontend-next/hooks/index.js` to export:
   ```javascript
   export { useSocket } from './useSocket';
   ```

---

### Step 1.3: Update Frontend Page to Use WebSocket

**File**: `frontend-next/pages/index.js`

**Action**: Update to display real-time updates

```javascript
import { useState, useEffect } from 'react';
import { useSocket } from '../hooks/useSocket';

export default function Home() {
  const [raceId] = useState(1); // You can make this dynamic
  const { isConnected, updates } = useSocket(raceId);
  const [latestUpdate, setLatestUpdate] = useState(null);
  
  useEffect(() => {
    if (updates.length > 0) {
      setLatestUpdate(updates[updates.length - 1]);
    }
  }, [updates]);
  
  return (
    <div style={{ padding: 20 }}>
      <h1>GR Race Guardian — Live Dashboard</h1>
      
      {/* Connection Status */}
      <div style={{ marginBottom: 20 }}>
        <span style={{ 
          padding: '5px 10px', 
          backgroundColor: isConnected ? 'green' : 'red',
          color: 'white',
          borderRadius: 5
        }}>
          {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
        </span>
      </div>
      
      {/* Latest Update */}
      {latestUpdate && (
        <div style={{ 
          border: '1px solid #ccc', 
          padding: 15, 
          borderRadius: 5,
          marginBottom: 20
        }}>
          <h2>Latest Race Update</h2>
          <p><strong>Time:</strong> {new Date(latestUpdate.timestamp).toLocaleTimeString()}</p>
          
          {latestUpdate.drivers && (
            <div>
              <h3>Driver Positions:</h3>
              <ul>
                {latestUpdate.drivers.map((driver, idx) => (
                  <li key={idx}>
                    {driver.id}: Lap {driver.lap}, {driver.lapTime.toFixed(3)}s, 
                    Position {driver.position}, Sector {driver.sector}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
      
      {/* Update History */}
      <div>
        <h2>Update History ({updates.length} updates)</h2>
        <div style={{ 
          maxHeight: 300, 
          overflowY: 'auto',
          border: '1px solid #ccc',
          padding: 10
        }}>
          {updates.map((update, idx) => (
            <div key={idx} style={{ 
              padding: 5, 
              borderBottom: '1px solid #eee',
              fontSize: '0.9em'
            }}>
              {new Date(update.timestamp).toLocaleTimeString()}: 
              {update.drivers?.length || 0} drivers
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

**Next Steps**:
1. Save this file
2. Start frontend: `cd frontend-next && npm run dev`
3. Open browser to `http://localhost:3000`
4. You should see connection status and live updates!

---

## ✅ Testing Your Implementation

### Test Checklist:

1. **Backend Server**:
   - [ ] Server starts without errors
   - [ ] Console shows "WebSocket server ready"
   - [ ] No port conflicts (3001)

2. **Frontend**:
   - [ ] Frontend starts without errors
   - [ ] Connection status shows "Connected" (green)
   - [ ] Updates appear in real-time
   - [ ] Update history grows

3. **Integration**:
   - [ ] Updates broadcast from backend
   - [ ] Frontend receives updates
   - [ ] No console errors

### Troubleshooting:

**If connection fails:**
- Check backend is running on port 3001
- Check CORS settings in backend
- Check browser console for errors
- Verify `socket.io-client` is installed: `npm list socket.io-client`

**If updates don't appear:**
- Check browser console for WebSocket messages
- Verify backend is broadcasting updates
- Check network tab for WebSocket connection

---

## 🎉 Next Steps

Once WebSocket is working:

1. **Connect to Real Data**: Replace simulated data with actual race data
2. **Add Visualizations**: Use Recharts to create charts (see Priority 1.2 in roadmap)
3. **Add More Features**: Continue with other features from [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md)

---

## 📚 Learn More

- Full roadmap: [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md)
- Tech stack: [TECH_STACK.md](TECH_STACK.md)
- Socket.IO docs: https://socket.io/docs/v4/

---

**Ready to start? Follow the steps above and you'll have real-time updates working in 1-2 hours! 🚀**

