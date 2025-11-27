/**
 * Authentication Service
 * 
 * JWT-based authentication for GR Race Guardian
 */
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');

// In production, use environment variable
const JWT_SECRET = process.env.JWT_SECRET || 'gr-race-guardian-secret-key-change-in-production';
const JWT_EXPIRES_IN = process.env.JWT_EXPIRES_IN || '24h';

// In-memory user storage (replace with database in production)
const users = [
  {
    id: 1,
    username: 'admin',
    email: 'admin@raceguardian.com',
    password: '$2a$10$rOzJcZrNhqK8v7OvQaFz7uQ9zE3Y7hQxK7yVKxR9zQ7zQ7zQ7zQ7z', // 'admin123'
    role: 'admin',
    createdAt: new Date().toISOString()
  }
];

class AuthService {
  /**
   * Register a new user
   */
  async register(username, email, password) {
    // Check if user already exists
    const existingUser = users.find(u => u.username === username || u.email === email);
    if (existingUser) {
      throw new Error('User already exists');
    }

    // Hash password
    const hashedPassword = await bcrypt.hash(password, 10);

    // Create user
    const newUser = {
      id: users.length + 1,
      username,
      email,
      password: hashedPassword,
      role: 'user',
      createdAt: new Date().toISOString()
    };

    users.push(newUser);

    // Generate token
    const token = this.generateToken(newUser);

    return {
      user: {
        id: newUser.id,
        username: newUser.username,
        email: newUser.email,
        role: newUser.role
      },
      token
    };
  }

  /**
   * Login user
   */
  async login(username, password) {
    // Find user
    const user = users.find(u => u.username === username || u.email === username);
    if (!user) {
      throw new Error('Invalid credentials');
    }

    // Verify password
    const isValid = await bcrypt.compare(password, user.password);
    if (!isValid) {
      throw new Error('Invalid credentials');
    }

    // Generate token
    const token = this.generateToken(user);

    return {
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        role: user.role
      },
      token
    };
  }

  /**
   * Generate JWT token
   */
  generateToken(user) {
    return jwt.sign(
      {
        id: user.id,
        username: user.username,
        email: user.email,
        role: user.role
      },
      JWT_SECRET,
      { expiresIn: JWT_EXPIRES_IN }
    );
  }

  /**
   * Verify JWT token
   */
  verifyToken(token) {
    try {
      return jwt.verify(token, JWT_SECRET);
    } catch (error) {
      return null;
    }
  }

  /**
   * Get user by ID
   */
  getUserById(id) {
    const user = users.find(u => u.id === parseInt(id));
    if (!user) {
      return null;
    }
    return {
      id: user.id,
      username: user.username,
      email: user.email,
      role: user.role
    };
  }

  /**
   * Get all users (admin only)
   */
  getAllUsers() {
    return users.map(u => ({
      id: u.id,
      username: u.username,
      email: u.email,
      role: u.role,
      createdAt: u.createdAt
    }));
  }
}

module.exports = new AuthService();

