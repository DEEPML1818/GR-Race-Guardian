/**
 * Job Queue Routes
 * 
 * API endpoints for managing Bull Queue jobs
 */

const express = require('express');
const router = express.Router();
const {
  addSimulationJob,
  addPredictionJob,
  getJobStatus,
  getJobResult,
  getQueueStats,
  checkRedisConnection
} = require('../queues/simulation-queue');

/**
 * GET /api/jobs/stats
 * Get queue statistics
 */
router.get('/stats', async (req, res) => {
  try {
    const stats = await getQueueStats();
    res.json({
      success: true,
      ...stats
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * GET /api/jobs/health
 * Check if Redis is connected
 */
router.get('/health', async (req, res) => {
  const connected = await checkRedisConnection();
  res.json({
    success: connected,
    redisConnected: connected,
    message: connected ? 'Redis is connected' : 'Redis is not connected. Jobs will not be queued.'
  });
});

/**
 * POST /api/jobs/simulate
 * Add a simulation job to the queue
 */
router.post('/simulate', async (req, res) => {
  try {
    // Check Redis connection
    const connected = await checkRedisConnection();
    if (!connected) {
      return res.status(503).json({
        success: false,
        error: 'Redis is not connected. Please start Redis server to use job queues.',
        fallback: 'Use direct simulation endpoint instead'
      });
    }

    const { raceParams, driverData, strategyOptions } = req.body;
    
    const job = await addSimulationJob({
      raceParams: raceParams || {},
      driverData: driverData || [],
      strategyOptions: strategyOptions || {}
    });
    
    res.json({
      success: true,
      jobId: job.id,
      message: 'Simulation job queued',
      statusUrl: `/api/jobs/simulations/${job.id}`
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * POST /api/jobs/predict
 * Add a prediction job to the queue
 */
router.post('/predict', async (req, res) => {
  try {
    const connected = await checkRedisConnection();
    if (!connected) {
      return res.status(503).json({
        success: false,
        error: 'Redis is not connected'
      });
    }

    const { features } = req.body;
    
    if (!features) {
      return res.status(400).json({
        success: false,
        error: 'Features are required'
      });
    }
    
    const job = await addPredictionJob({ features });
    
    res.json({
      success: true,
      jobId: job.id,
      message: 'Prediction job queued',
      statusUrl: `/api/jobs/predictions/${job.id}`
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * GET /api/jobs/simulations/:id
 * Get simulation job status
 */
router.get('/simulations/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const status = await getJobStatus('simulations', id);
    
    if (!status) {
      return res.status(404).json({
        success: false,
        error: 'Job not found'
      });
    }
    
    res.json({
      success: true,
      ...status
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * GET /api/jobs/predictions/:id
 * Get prediction job status
 */
router.get('/predictions/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const status = await getJobStatus('predictions', id);
    
    if (!status) {
      return res.status(404).json({
        success: false,
        error: 'Job not found'
      });
    }
    
    res.json({
      success: true,
      ...status
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * GET /api/jobs/simulations/:id/result
 * Get simulation job result
 */
router.get('/simulations/:id/result', async (req, res) => {
  try {
    const { id } = req.params;
    const result = await getJobResult('simulations', id);
    res.json({
      success: true,
      ...result
    });
  } catch (error) {
    res.status(404).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * GET /api/jobs/predictions/:id/result
 * Get prediction job result
 */
router.get('/predictions/:id/result', async (req, res) => {
  try {
    const { id } = req.params;
    const result = await getJobResult('predictions', id);
    res.json({
      success: true,
      ...result
    });
  } catch (error) {
    res.status(404).json({
      success: false,
      error: error.message
    });
  }
});

module.exports = router;

