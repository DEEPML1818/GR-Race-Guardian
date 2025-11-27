const express = require('express');
const { createServer } = require('http');
const { Server } = require('socket.io');
const bodyParser = require('body-parser');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const { spawn } = require('child_process');
const path = require('path');
const axios = require('axios');
const { setupLogging } = require('./utils/logger');

// Import AI routes
const aiRoutes = require('./routes/ai-route');

// Import Auth routes
const authRoutes = require('./routes/auth-route');

// Import Job Queue routes
const jobsRoutes = require('./routes/jobs-route');

// Import queue manager (will create this next)
// const { createSimulationJob } = require('./queues/simulation-queue');

// Load environment variables
require('dotenv').config();

// Setup logging
const logger = setupLogging(process.env.LOG_LEVEL || 'INFO');

const app = express();
const httpServer = createServer(app);
const io = new Server(httpServer, {
  cors: {
    origin: ["http://localhost:3000", "http://localhost:3001"],
    methods: ["GET", "POST"]
  }
});

// Middleware
app.use(cors());
app.use(bodyParser.json());

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
});
app.use('/api/', limiter);

// Config
const PYTHON_DIR = path.join(__dirname, '..', 'backend-python');
const PYTHON_CMD = process.env.PYTHON || 'python';
const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:8000';

// WebSocket connection handler
io.on('connection', (socket) => {
  logger.info(`WebSocket client connected: ${socket.id}`);
  
  // Subscribe to race updates
  socket.on('subscribe-race', (raceId) => {
    socket.join(`race-${raceId}`);
    logger.info(`Client ${socket.id} subscribed to race ${raceId}`);
    socket.emit('subscribed', { raceId, message: `Subscribed to race ${raceId}` });
  });
  
  // Unsubscribe
  socket.on('unsubscribe-race', (raceId) => {
    socket.leave(`race-${raceId}`);
    logger.info(`Client ${socket.id} unsubscribed from race ${raceId}`);
  });
  
  // Request driver metrics
  socket.on('request-metrics', async (data) => {
    const { driverId, raceId } = data;
    try {
      const metrics = await getDriverMetrics(driverId, raceId);
      socket.emit('driver-metrics', { driverId, metrics });
    } catch (error) {
      socket.emit('error', { message: error.message });
    }
  });
  
  // Disconnect handler
  socket.on('disconnect', () => {
    logger.info(`WebSocket client disconnected: ${socket.id}`);
  });
});

// Import live data packet generator
const liveDataPacket = require('./services/live-data-packet');

// Broadcast race updates (simulated - replace with real data source)
let simulationInterval = null;
async function startRaceSimulation(raceId = 1) {
  if (simulationInterval) return; // Already running
  
  let lap = 1;
  const drivers = [
    { id: 'driver_1', baseTime: 95.0, position: 1, sector: 'S1', tire_age: 10, tire_compound: 'MEDIUM' },
    { id: 'driver_2', baseTime: 95.5, position: 2, sector: 'S1', tire_age: 8, tire_compound: 'SOFT' },
    { id: 'driver_3', baseTime: 96.0, position: 3, sector: 'S1', tire_age: 12, tire_compound: 'MEDIUM' }
  ];
  
  simulationInterval = setInterval(async () => {
    // Update drivers
    const updatedDrivers = drivers.map((driver, idx) => {
      // Simulate lap time with variation and degradation
      const degradation = driver.tire_age * 0.002;
      const lapTime = driver.baseTime * (1 + degradation) + (Math.random() - 0.5) * 2;
      driver.tire_age += 1;
      
      return {
        ...driver,
        lapTime: parseFloat(lapTime.toFixed(3)),
        sector: ['S1', 'S2', 'S3'][(lap + idx) % 3],
        deltaToLeader: idx === 0 ? 0 : lapTime - drivers[0].baseTime,
        lap_times: [lapTime],
        sector_times: [
          { S1: lapTime / 3, S2: lapTime / 3, S3: lapTime / 3 }
        ],
        current_lap: lap
      };
    });

      // Generate unified live data packet
      try {
        const livePacket = await liveDataPacket.generateLiveDataPacket({
          timestamp: new Date().toISOString(),
          lap: lap,
          drivers: updatedDrivers,
          race_id: `race_${raceId}`,
          total_laps: 50
        });

        // Broadcast unified packet to all subscribers (multiple events for compatibility)
        io.to(`race-${raceId}`).emit('race-update', livePacket);
        io.to(`race-${raceId}`).emit('live-data-packet', livePacket);
        io.emit('live-data-packet', livePacket); // Broadcast to all clients
        
        // Also broadcast individual components if needed
        if (livePacket.driverTwin) {
          Object.keys(livePacket.driverTwin).forEach(driverId => {
            io.emit('driver-twin-update', {
              driver_id: driverId,
              twin: livePacket.driverTwin[driverId],
              timestamp: livePacket.timestamp
            });
          });
        }
        
        if (livePacket.raceTwin) {
          io.emit('race-twin-update', {
            race_id: `race_${raceId}`,
            race_twin: livePacket.raceTwin,
            timestamp: livePacket.timestamp
          });
        }
      } catch (error) {
        logger.error('Error generating live data packet:', error);
        // Fallback to simple update
        io.to(`race-${raceId}`).emit('race-update', {
          timestamp: new Date().toISOString(),
          lap: lap,
          drivers: updatedDrivers
        });
      }
    
    lap++;
    
    // Stop after 50 laps (demo)
    if (lap > 50) {
      stopRaceSimulation();
    }
  }, 1000); // Update every second
}

function stopRaceSimulation() {
  if (simulationInterval) {
    clearInterval(simulationInterval);
    simulationInterval = null;
  }
}

// API Routes

// AI Race Engineer routes
app.use('/api/ai', aiRoutes);

// Authentication routes
app.use('/api/auth', authRoutes);

// Job Queue routes
app.use('/api/jobs', jobsRoutes);

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Start/stop race simulation
app.post('/api/race/start', (req, res) => {
  const { raceId } = req.body;
  startRaceSimulation(raceId || 1);
  res.json({ success: true, message: `Race simulation started for race ${raceId || 1}` });
});

app.post('/api/race/stop', (req, res) => {
  stopRaceSimulation();
  res.json({ success: true, message: 'Race simulation stopped' });
});

// Prediction endpoint (calls Python service)
app.post('/api/predict', async (req, res) => {
  const csv = req.body.csv;
  if (!csv) {
    return res.status(400).json({ error: 'missing csv path in body' });
  }

  try {
    // Try FastAPI endpoint first
    const response = await axios.post(`${PYTHON_API_URL}/predict`, {
      csv: csv,
      model_path: req.body.model_path || 'models/merged_road_model.joblib'
    }, { timeout: 30000 });
    
    res.json({ code: 0, payload: response.data });
  } catch (error) {
    // Fallback to spawn method
    const script = path.join(PYTHON_DIR, 'serve_model.py');
    const modelPath = path.join(PYTHON_DIR, 'models', 'model.joblib');
    const args = [script, '--csv', csv, '--model', modelPath];

    const py = spawn(PYTHON_CMD, args, { cwd: PYTHON_DIR });
    let out = '';
    let err = '';
    
    py.stdout.on('data', (data) => { out += data.toString(); });
    py.stderr.on('data', (data) => { err += data.toString(); });
    
    py.on('close', (code) => {
      if (err) console.error('python stderr', err);
      try {
        const payload = JSON.parse(out);
        res.json({ code, payload });
      } catch (e) {
        res.status(500).json({ error: 'failed to parse python output', out, err, code });
      }
    });
  }
});

// Driver metrics endpoint
async function getDriverMetrics(driverId, raceId) {
  // This will be implemented with database or file system
  return {
    consistencyIndex: 0.92,
    aggressionScore: 0.65,
    sectorStrength: {
      S1: 0.95,
      S2: 0.88,
      S3: 0.91
    }
  };
}

app.post('/api/driver/metrics', async (req, res) => {
  const { driverId, raceId } = req.body;
  try {
    const metrics = await getDriverMetrics(driverId, raceId);
    res.json({ driverId, metrics });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Sector timing endpoint
app.post('/api/sectors/analyze', async (req, res) => {
  // Will call Python service for sector analysis
  res.json({ message: 'Sector analysis endpoint - to be implemented' });
});

// Monte Carlo simulation endpoint
app.post('/api/simulate', async (req, res) => {
  const { driverPaces, nLaps, iterations } = req.body;
  
  try {
    // Call Python Monte Carlo service
    const response = await axios.post(`${PYTHON_API_URL}/simulate`, {
      driver_paces: driverPaces,
      n_laps: nLaps || 50,
      iterations: iterations || 1000
    }, { timeout: 60000 });
    
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Race pace prediction endpoint
app.post('/api/pace/predict', async (req, res) => {
  try {
    const response = await axios.post(`${PYTHON_API_URL}/pace/predict`, req.body, { timeout: 30000 });
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Driver Twin update loop endpoint
app.post('/api/driver-twin/update', async (req, res) => {
  try {
    const { driver_id, twin, timestamp } = req.body;
    
    // Store twin in cache
    if (driver_id && twin) {
      // Broadcast to WebSocket clients
      io.emit('driver-twin-update', {
        driver_id,
        twin,
        timestamp: timestamp || new Date().toISOString()
      });
    }
    
    res.json({ success: true, message: 'Driver Twin update received' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Pit rejoin simulation endpoint
app.post('/api/strategy/pit-rejoin', async (req, res) => {
  try {
    const response = await axios.post(
      `${PYTHON_API_URL}/strategy/pit-rejoin`,
      req.body,
      { timeout: 30000 }
    );
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get Driver Twin from loop
app.get('/api/driver-twin/loop/:driverId', async (req, res) => {
  try {
    const { driverId } = req.params;
    const response = await axios.get(
      `${PYTHON_API_URL}/driver-twin/loop/${driverId}`,
      { timeout: 10000 }
    );
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Simulate Race Twin
app.post('/api/race-twin/simulate', async (req, res) => {
  try {
    const response = await axios.post(
      `${PYTHON_API_URL}/race-twin/simulate`,
      req.body,
      { timeout: 60000 } // Race simulation can take time
    );
    
    // Broadcast to WebSocket clients if successful
    if (response.data.success && response.data.race_twin) {
      const raceId = req.body.race_id || 'race_1';
      io.emit('race-twin-update', {
        race_id: raceId,
        race_twin: response.data.race_twin,
        timestamp: new Date().toISOString()
      });
    }
    
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get Race Twin
app.get('/api/race-twin/:raceId', async (req, res) => {
  try {
    const { raceId } = req.params;
    const response = await axios.get(
      `${PYTHON_API_URL}/race-twin/${raceId}`,
      { timeout: 30000 }
    );
    
    // Broadcast to WebSocket clients if successful
    if (response.data.success && response.data.race_twin) {
      io.emit('race-twin-update', {
        race_id: raceId,
        race_twin: response.data.race_twin,
        timestamp: response.data.timestamp || new Date().toISOString()
      });
    }
    
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Generate unified live data packet
app.post('/api/live-data-packet', async (req, res) => {
  try {
    const raceData = req.body;
    const packet = await liveDataPacket.generateLiveDataPacket(raceData);
    
    // Broadcast unified packet to WebSocket clients
    const raceId = raceData.race_id || 'race_1';
    io.to(`race-${raceId}`).emit('live-data-packet', packet);
    io.emit('live-data-packet', packet); // Also broadcast to all
    
    res.json(packet);
  } catch (error) {
    logger.error('Error generating live data packet:', error);
    res.status(500).json({ error: error.message });
  }
});

// Strategy Console Endpoints
app.post('/api/strategy/pit-window-timeline', async (req, res) => {
  try {
    const response = await axios.post(
      `${PYTHON_API_URL}/strategy/pit-window-timeline`,
      req.body,
      { timeout: 30000 }
    );
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/strategy/undercut-overcut', async (req, res) => {
  try {
    const response = await axios.post(
      `${PYTHON_API_URL}/strategy/undercut-overcut`,
      req.body,
      { timeout: 30000 }
    );
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/strategy/risk-score', async (req, res) => {
  try {
    const response = await axios.post(
      `${PYTHON_API_URL}/strategy/risk-score`,
      req.body,
      { timeout: 30000 }
    );
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/strategy/tire-life-prediction', async (req, res) => {
  try {
    const response = await axios.post(
      `${PYTHON_API_URL}/strategy/tire-life-prediction`,
      req.body,
      { timeout: 30000 }
    );
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/strategy/rejoin-window', async (req, res) => {
  try {
    const response = await axios.post(
      `${PYTHON_API_URL}/strategy/rejoin-window`,
      req.body,
      { timeout: 30000 }
    );
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Track Map Endpoints
app.get('/api/track/coordinates', async (req, res) => {
  try {
    const trackName = req.query.track_name;
    const response = await axios.get(
      `${PYTHON_API_URL}/track/coordinates${trackName ? `?track_name=${trackName}` : ''}`,
      { timeout: 10000 }
    );
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/track/driver-positions', async (req, res) => {
  try {
    const response = await axios.post(
      `${PYTHON_API_URL}/track/driver-positions`,
      req.body,
      { timeout: 30000 }
    );
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/track/traffic-density', async (req, res) => {
  try {
    const response = await axios.post(
      `${PYTHON_API_URL}/track/traffic-density`,
      req.body,
      { timeout: 30000 }
    );
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/track/pit-rejoin-ghost', async (req, res) => {
  try {
    const response = await axios.post(
      `${PYTHON_API_URL}/track/pit-rejoin-ghost`,
      req.body,
      { timeout: 30000 }
    );
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/track/heatmap', async (req, res) => {
  try {
    const response = await axios.post(
      `${PYTHON_API_URL}/track/heatmap`,
      req.body,
      { timeout: 30000 }
    );
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Start server
const PORT = process.env.PORT || 3001;
httpServer.listen(PORT, () => {
  logger.info(`Node.js API server listening on port ${PORT}`);
  logger.info(`WebSocket server ready`);
  logger.info(`Frontend should connect to: ws://localhost:${PORT}`);
  logger.info(`Start race simulation: POST /api/race/start`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  stopRaceSimulation();
  httpServer.close(() => {
    logger.info('Server closed');
    logger.close();
    process.exit(0);
  });
});

// Error handling
process.on('uncaughtException', (error) => {
  logger.critical('Uncaught exception', { error: error.message, stack: error.stack });
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled rejection', { reason, promise });
});
