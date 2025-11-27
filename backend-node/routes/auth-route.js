/**
 * Authentication Routes
 * 
 * Login, register, and user management endpoints
 */
const express = require('express');
const router = express.Router();
const authService = require('../services/auth-service');
const { authenticateToken, requireAdmin } = require('../middleware/auth-middleware');

/**
 * POST /api/auth/register
 * Register a new user
 */
router.post('/register', async (req, res) => {
  try {
    const { username, email, password } = req.body;

    if (!username || !email || !password) {
      return res.status(400).json({ 
        error: 'Username, email, and password are required' 
      });
    }

    if (password.length < 6) {
      return res.status(400).json({ 
        error: 'Password must be at least 6 characters' 
      });
    }

    const result = await authService.register(username, email, password);
    
    res.status(201).json({
      success: true,
      message: 'User registered successfully',
      ...result
    });
  } catch (error) {
    res.status(400).json({ 
      error: error.message || 'Registration failed' 
    });
  }
});

/**
 * POST /api/auth/login
 * Login user
 */
router.post('/login', async (req, res) => {
  try {
    const { username, password } = req.body;

    if (!username || !password) {
      return res.status(400).json({ 
        error: 'Username and password are required' 
      });
    }

    const result = await authService.login(username, password);
    
    res.json({
      success: true,
      message: 'Login successful',
      ...result
    });
  } catch (error) {
    res.status(401).json({ 
      error: error.message || 'Login failed' 
    });
  }
});

/**
 * GET /api/auth/me
 * Get current user info (protected)
 */
router.get('/me', authenticateToken, (req, res) => {
  const user = authService.getUserById(req.user.id);
  if (!user) {
    return res.status(404).json({ error: 'User not found' });
  }
  res.json({
    success: true,
    user
  });
});

/**
 * POST /api/auth/verify
 * Verify JWT token
 */
router.post('/verify', (req, res) => {
  const { token } = req.body;
  
  if (!token) {
    return res.status(400).json({ error: 'Token required' });
  }

  const decoded = authService.verifyToken(token);
  if (!decoded) {
    return res.status(401).json({ 
      success: false,
      error: 'Invalid or expired token' 
    });
  }

  res.json({
    success: true,
    user: decoded
  });
});

/**
 * GET /api/auth/users
 * Get all users (admin only)
 */
router.get('/users', authenticateToken, requireAdmin, (req, res) => {
  const users = authService.getAllUsers();
  res.json({
    success: true,
    users
  });
});

module.exports = router;

