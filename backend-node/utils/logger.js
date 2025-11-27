/**
 * Unified Logging System for Node.js Backend
 * 
 * Provides structured logging with file and console output.
 */

const fs = require('fs');
const path = require('path');
const { createWriteStream } = require('fs');

class Logger {
  constructor(logLevel = 'INFO', logDir = 'logs') {
    this.logLevel = logLevel;
    this.logDir = logDir;
    this.logFile = null;
    this.logStream = null;
    
    // Create log directory
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
    
    // Create log file
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    this.logFile = path.join(logDir, `race_guardian_${timestamp}.log`);
    this.logStream = createWriteStream(this.logFile, { flags: 'a' });
    
    // Log levels
    this.levels = {
      DEBUG: 0,
      INFO: 1,
      WARNING: 2,
      ERROR: 3,
      CRITICAL: 4
    };
    
    this.currentLevel = this.levels[logLevel] || this.levels.INFO;
  }
  
  _formatMessage(level, message, context = null) {
    const timestamp = new Date().toISOString();
    let logMessage = `[${timestamp}] [${level}] ${message}`;
    
    if (context) {
      logMessage += ` | Context: ${JSON.stringify(context)}`;
    }
    
    return logMessage;
  }
  
  _log(level, message, context = null) {
    const levelNum = this.levels[level] || this.levels.INFO;
    
    if (levelNum >= this.currentLevel) {
      const formatted = this._formatMessage(level, message, context);
      
      // Console output
      if (levelNum >= this.levels.ERROR) {
        console.error(formatted);
      } else if (levelNum >= this.levels.WARNING) {
        console.warn(formatted);
      } else {
        console.log(formatted);
      }
      
      // File output
      if (this.logStream) {
        this.logStream.write(formatted + '\n');
      }
    }
  }
  
  debug(message, context = null) {
    this._log('DEBUG', message, context);
  }
  
  info(message, context = null) {
    this._log('INFO', message, context);
  }
  
  warning(message, context = null) {
    this._log('WARNING', message, context);
  }
  
  error(message, context = null) {
    this._log('ERROR', message, context);
  }
  
  critical(message, context = null) {
    this._log('CRITICAL', message, context);
  }
  
  logApiCall(method, endpoint, status, duration, context = null) {
    const message = `API ${method} ${endpoint} - Status: ${status} - Duration: ${duration}ms`;
    this.info(message, context);
  }
  
  logError(error, context = null) {
    const errorContext = {
      ...context,
      error: {
        name: error.name,
        message: error.message,
        stack: error.stack
      }
    };
    this.error(`Error: ${error.name}: ${error.message}`, errorContext);
  }
  
  close() {
    if (this.logStream) {
      this.logStream.end();
    }
  }
}

// Global logger instance
let globalLogger = null;

function getLogger(logLevel = 'INFO') {
  if (!globalLogger) {
    globalLogger = new Logger(logLevel);
  }
  return globalLogger;
}

function setupLogging(logLevel = 'INFO') {
  globalLogger = new Logger(logLevel);
  return globalLogger;
}

module.exports = {
  Logger,
  getLogger,
  setupLogging
};

