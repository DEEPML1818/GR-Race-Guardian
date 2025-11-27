/**
 * Bull Queue for Heavy Python Jobs
 * 
 * Handles queuing of simulation and prediction jobs
 * Redis is OPTIONAL - server works without it
 */

const { Queue, Worker } = require('bullmq');
const Redis = require('ioredis');
const { spawn } = require('child_process');
const path = require('path');

// Redis connection - OPTIONAL
let connection = null;
let redisAvailable = false;
let queuesInitialized = false;

// Check if Redis is available (non-blocking)
async function checkRedisAvailable() {
  return new Promise((resolve) => {
    const testConnection = new Redis({
      host: process.env.REDIS_HOST || 'localhost',
      port: process.env.REDIS_PORT || 6379,
      connectTimeout: 500,
      lazyConnect: false,
      retryStrategy: () => null, // Don't retry
      maxRetriesPerRequest: null,
      enableOfflineQueue: false
    });

    const timeout = setTimeout(() => {
      testConnection.disconnect();
      resolve(false);
    }, 500);

    testConnection.on('error', () => {
      clearTimeout(timeout);
      testConnection.disconnect();
      resolve(false);
    });

    testConnection.on('connect', () => {
      clearTimeout(timeout);
      testConnection.disconnect();
      resolve(true);
    });
  });
}

// Initialize Redis connection only if available
(async () => {
  try {
    redisAvailable = await checkRedisAvailable();
    
    if (redisAvailable) {
      connection = new Redis({
        host: process.env.REDIS_HOST || 'localhost',
        port: process.env.REDIS_PORT || 6379,
        retryStrategy: (times) => {
          if (times > 3) return null;
          return Math.min(times * 50, 2000);
        },
        maxRetriesPerRequest: null,
        enableOfflineQueue: false,
        connectTimeout: 2000
      });

      // Suppress connection errors
      connection.on('error', () => {
        // Silently ignore - Redis is optional
      });

      console.log('[Queue] Redis connection initialized');
    } else {
      console.warn('[Queue] Redis not available. Queue system disabled. Server continues normally.');
    }
  } catch (error) {
    // Silently ignore - Redis is optional
    connection = null;
    redisAvailable = false;
  }
})();

// Queue instances
let simulationQueue = null;
let predictionQueue = null;

// Initialize queues after Redis check
setTimeout(() => {
  if (connection && redisAvailable) {
    try {
      simulationQueue = new Queue('simulations', { connection });
      predictionQueue = new Queue('predictions', { connection });
      queuesInitialized = true;
      console.log('[Queue] Queues initialized successfully');
    } catch (error) {
      // Silently ignore
    }
  }
}, 150);

/**
 * Add a Monte Carlo simulation job to the queue
 */
async function addSimulationJob(data) {
  if (!simulationQueue || !redisAvailable) {
    throw new Error('Queue not available. Redis may not be connected.');
  }
  
  const job = await simulationQueue.add(
    'monte-carlo',
    {
      ...data,
      timestamp: new Date().toISOString()
    },
    {
      attempts: 3,
      backoff: {
        type: 'exponential',
        delay: 2000
      },
      removeOnComplete: {
        age: 3600,
        count: 100
      },
      removeOnFail: {
        age: 86400
      }
    }
  );
  
  return job;
}

/**
 * Add a prediction job to the queue
 */
async function addPredictionJob(data) {
  if (!predictionQueue || !redisAvailable) {
    throw new Error('Queue not available. Redis may not be connected.');
  }
  
  const job = await predictionQueue.add(
    'predict',
    {
      ...data,
      timestamp: new Date().toISOString()
    },
    {
      attempts: 3,
      backoff: {
        type: 'exponential',
        delay: 1000
      },
      removeOnComplete: {
        age: 3600
      }
    }
  );
  
  return job;
}

/**
 * Get job status by ID
 */
async function getJobStatus(queueName, jobId) {
  const queue = queueName === 'simulations' ? simulationQueue : predictionQueue;
  
  if (!queue || !redisAvailable) {
    throw new Error('Queue not available. Redis may not be connected.');
  }
  
  const job = await queue.getJob(jobId);
  
  if (!job) {
    return null;
  }
  
  const state = await job.getState();
  const progress = job.progress || 0;
  
  return {
    id: job.id,
    name: job.name,
    state,
    progress,
    data: job.data,
    result: job.returnvalue,
    error: job.failedReason,
    createdAt: new Date(job.timestamp),
    processedAt: job.processedOn ? new Date(job.processedOn) : null,
    finishedAt: job.finishedOn ? new Date(job.finishedOn) : null
  };
}

/**
 * Get job result by ID
 */
async function getJobResult(queueName, jobId) {
  const queue = queueName === 'simulations' ? simulationQueue : predictionQueue;
  
  if (!queue || !redisAvailable) {
    throw new Error('Queue not available. Redis may not be connected.');
  }
  
  const job = await queue.getJob(jobId);
  
  if (!job) {
    throw new Error('Job not found');
  }
  
  const state = await job.getState();
  
  if (state === 'completed') {
    return {
      status: 'completed',
      result: job.returnvalue,
      jobId: job.id
    };
  } else if (state === 'failed') {
    return {
      status: 'failed',
      error: job.failedReason,
      jobId: job.id
    };
  } else {
    return {
      status: state,
      message: 'Job is still processing',
      jobId: job.id
    };
  }
}

/**
 * Workers - Only create if Redis is available
 */
let simulationWorker = null;
let predictionWorker = null;

// Create workers only if Redis is available
setTimeout(() => {
  if (connection && simulationQueue && redisAvailable && queuesInitialized) {
    try {
      simulationWorker = new Worker(
        'simulations',
        async (job) => {
          const { raceParams, driverData, strategyOptions } = job.data;
          
          console.log(`[Worker] Processing simulation job ${job.id}`);
          
          await job.updateProgress(10);
          
          return new Promise((resolve, reject) => {
            const pythonScript = path.join(__dirname, '../../backend-python/scripts/run_simulation.py');
            const pythonProcess = spawn('python', [
              pythonScript,
              JSON.stringify({ raceParams, driverData, strategyOptions })
            ]);
            
            let output = '';
            let errorOutput = '';
            
            pythonProcess.stdout.on('data', (data) => {
              output += data.toString();
              if (output.includes('Progress:')) {
                const match = output.match(/Progress: (\d+)/);
                if (match) {
                  job.updateProgress(parseInt(match[1]));
                }
              }
            });
            
            pythonProcess.stderr.on('data', (data) => {
              errorOutput += data.toString();
            });
            
            pythonProcess.on('close', (code) => {
              if (code === 0) {
                try {
                  const result = JSON.parse(output);
                  resolve(result);
                } catch (e) {
                  resolve({ output, raw: true });
                }
              } else {
                reject(new Error(`Simulation failed: ${errorOutput || 'Unknown error'}`));
              }
            });
            
            pythonProcess.on('error', (error) => {
              reject(new Error(`Failed to start simulation: ${error.message}`));
            });
          });
        },
        {
          connection,
          concurrency: 2,
          limiter: {
            max: 5,
            duration: 60000
          }
        }
      );

      simulationWorker.on('completed', (job) => {
        console.log(`[Worker] Simulation job ${job.id} completed`);
      });

      simulationWorker.on('failed', (job, err) => {
        console.error(`[Worker] Simulation job ${job.id} failed:`, err.message);
      });
    } catch (error) {
      // Silently ignore Worker creation errors
    }
  }

  if (connection && predictionQueue && redisAvailable && queuesInitialized) {
    try {
      predictionWorker = new Worker(
        'predictions',
        async (job) => {
          const { features } = job.data;
          
          console.log(`[Worker] Processing prediction job ${job.id}`);
          
          await job.updateProgress(50);
          
          const axios = require('axios');
          try {
            const response = await axios.post('http://localhost:8000/predict', {
              features
            });
            
            await job.updateProgress(100);
            return response.data;
          } catch (error) {
            throw new Error(`Prediction failed: ${error.message}`);
          }
        },
        {
          connection,
          concurrency: 5,
          limiter: {
            max: 20,
            duration: 60000
          }
        }
      );

      predictionWorker.on('completed', (job) => {
        console.log(`[Worker] Prediction job ${job.id} completed`);
      });

      predictionWorker.on('failed', (job, err) => {
        console.error(`[Worker] Prediction job ${job.id} failed:`, err.message);
      });
    } catch (error) {
      // Silently ignore Worker creation errors
    }
  }
}, 300);

/**
 * Check if Redis is connected
 */
async function checkRedisConnection() {
  try {
    if (!connection || !redisAvailable) {
      return false;
    }
    const pingPromise = connection.ping();
    const timeoutPromise = new Promise((_, reject) => 
      setTimeout(() => reject(new Error('Timeout')), 1000)
    );
    await Promise.race([pingPromise, timeoutPromise]);
    return true;
  } catch (error) {
    return false;
  }
}

/**
 * Get queue statistics
 */
async function getQueueStats() {
  try {
    if (!simulationQueue || !predictionQueue || !redisAvailable) {
      return {
        error: 'Queues not available. Redis may not be connected.',
        redisConnected: false
      };
    }
    
    const simulationStats = {
      waiting: await simulationQueue.getWaitingCount(),
      active: await simulationQueue.getActiveCount(),
      completed: await simulationQueue.getCompletedCount(),
      failed: await simulationQueue.getFailedCount()
    };
    
    const predictionStats = {
      waiting: await predictionQueue.getWaitingCount(),
      active: await predictionQueue.getActiveCount(),
      completed: await predictionQueue.getCompletedCount(),
      failed: await predictionQueue.getFailedCount()
    };
    
    return {
      simulations: simulationStats,
      predictions: predictionStats,
      redisConnected: await checkRedisConnection()
    };
  } catch (error) {
    return {
      error: error.message,
      redisConnected: false
    };
  }
}

module.exports = {
  simulationQueue,
  predictionQueue,
  addSimulationJob,
  addPredictionJob,
  getJobStatus,
  getJobResult,
  getQueueStats,
  checkRedisConnection,
  simulationWorker,
  predictionWorker
};
