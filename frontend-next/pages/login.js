'use client';

import { useState } from 'react';
import { useRouter } from 'next/router';

export default function Login() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:3001/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (response.ok && data.success) {
        // Store token
        localStorage.setItem('auth_token', data.token);
        localStorage.setItem('user', JSON.stringify(data.user));
        
        // Redirect to dashboard
        router.push('/');
      } else {
        setError(data.error || 'Login failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      backgroundColor: '#f5f5f5',
      padding: 20
    }}>
      <div style={{
        backgroundColor: 'white',
        padding: 40,
        borderRadius: 8,
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
        width: '100%',
        maxWidth: 400
      }}>
        <h1 style={{ marginTop: 0, color: '#333', textAlign: 'center' }}>
          🏎️ GR Race Guardian
        </h1>
        <h2 style={{ color: '#666', textAlign: 'center', fontSize: '18px', marginBottom: 30 }}>
          Login
        </h2>

        {error && (
          <div style={{
            padding: 10,
            backgroundColor: '#f8d7da',
            color: '#721c24',
            borderRadius: 4,
            marginBottom: 20,
            fontSize: '14px'
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 20 }}>
            <label style={{ display: 'block', marginBottom: 5, color: '#666', fontSize: '14px' }}>
              Username or Email
            </label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #ddd',
                borderRadius: 4,
                fontSize: '14px',
                boxSizing: 'border-box'
              }}
              placeholder="Enter username or email"
            />
          </div>

          <div style={{ marginBottom: 20 }}>
            <label style={{ display: 'block', marginBottom: 5, color: '#666', fontSize: '14px' }}>
              Password
            </label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #ddd',
                borderRadius: 4,
                fontSize: '14px',
                boxSizing: 'border-box'
              }}
              placeholder="Enter password"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '12px',
              backgroundColor: loading ? '#ccc' : '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: 4,
              fontSize: '16px',
              fontWeight: 'bold',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div style={{ marginTop: 20, textAlign: 'center' }}>
          <p style={{ color: '#666', fontSize: '14px' }}>
            Don't have an account?{' '}
            <a
              href="/signup"
              style={{ color: '#4CAF50', textDecoration: 'none' }}
            >
              Sign up
            </a>
          </p>
        </div>

        <div style={{ marginTop: 30, padding: 15, backgroundColor: '#f0f0f0', borderRadius: 4, fontSize: '12px', color: '#666' }}>
          <strong>Demo Credentials:</strong>
          <div style={{ marginTop: 5 }}>
            Username: <code>admin</code><br />
            Password: <code>admin123</code>
          </div>
        </div>
      </div>
    </div>
  );
}

