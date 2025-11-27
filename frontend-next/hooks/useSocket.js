import { useEffect, useRef, useState } from 'react';
import { io } from 'socket.io-client';

/**
 * WebSocket hook with auto-reconnect and error recovery
 */
export function useSocket(raceId, url = 'http://localhost:3001', options = {}) {
  const [isConnected, setIsConnected] = useState(false);
  const [updates, setUpdates] = useState([]);
  const [latestUpdate, setLatestUpdate] = useState(null);
  const [error, setError] = useState(null);
  const socketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = options.maxReconnectAttempts || 10;
  const reconnectDelay = options.reconnectDelay || 3000;

  useEffect(() => {
    // Initialize socket
    socketRef.current = io(url, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: reconnectDelay,
      reconnectionAttempts: maxReconnectAttempts,
      timeout: 5000,
      ...options
    });

    const socket = socketRef.current;

    // Connection handlers
    socket.on('connect', () => {
      console.log('[WebSocket] Connected');
      setIsConnected(true);
      setError(null);
      reconnectAttempts.current = 0;
      
      // Auto-subscribe to race if raceId provided
      if (raceId) {
        socket.emit('subscribe-race', raceId);
      }
    });

    socket.on('disconnect', (reason) => {
      console.log('[WebSocket] Disconnected:', reason);
      setIsConnected(false);
      
      // Auto-reconnect if not manual disconnect
      if (reason === 'io server disconnect') {
        // Server disconnected, reconnect manually
        socket.connect();
      }
    });

    socket.on('connect_error', (err) => {
      console.error('[WebSocket] Connection error:', err.message);
      setError(err.message);
      setIsConnected(false);
      
      // Enhanced exponential backoff for reconnection
      reconnectAttempts.current += 1;
      if (reconnectAttempts.current < maxReconnectAttempts) {
        const delay = Math.min(
          reconnectDelay * Math.pow(2, reconnectAttempts.current - 1),
          30000 // Max 30 seconds
        );
        
        console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current}/${maxReconnectAttempts})...`);
        
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('[WebSocket] Attempting reconnection...');
          socket.connect();
        }, delay);
      } else {
        console.error(`[WebSocket] Max reconnection attempts (${maxReconnectAttempts}) reached. Manual intervention required.`);
        setError(`Connection failed after ${maxReconnectAttempts} attempts. Please refresh the page.`);
      }
    });
    
    // Enhanced reconnection handling
    socket.on('reconnect', (attemptNumber) => {
      console.log(`[WebSocket] Reconnected after ${attemptNumber} attempts`);
      setIsConnected(true);
      setError(null);
      reconnectAttempts.current = 0;
      
      // Re-subscribe to race if needed
      if (raceId) {
        socket.emit('subscribe-race', raceId);
      }
    });
    
    socket.on('reconnect_attempt', (attemptNumber) => {
      console.log(`[WebSocket] Reconnection attempt ${attemptNumber}/${maxReconnectAttempts}`);
    });
    
    socket.on('reconnect_failed', () => {
      console.error('[WebSocket] Reconnection failed after all attempts');
      setError('Failed to reconnect. Please refresh the page.');
      setIsConnected(false);
    });

    // Message handlers
    socket.on('race-update', (data) => {
      setUpdates(prev => [...prev, data].slice(-100)); // Keep last 100 updates
      setLatestUpdate(data);
    });

    socket.on('driver-twin-update', (data) => {
      setLatestUpdate(prev => ({ ...prev, driverTwin: data }));
    });

    socket.on('error', (err) => {
      console.error('[WebSocket] Error:', err);
      setError(err.message || 'Unknown error');
    });

    // Cleanup
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (socket && raceId) {
        socket.emit('unsubscribe-race', raceId);
      }
      if (socket) {
        socket.disconnect();
      }
    };
  }, [url, raceId]);

  // Subscribe to race
  const subscribeRace = (raceId) => {
    if (socketRef.current && isConnected) {
      socketRef.current.emit('subscribe-race', raceId);
    }
  };

  // Unsubscribe from race
  const unsubscribeRace = (raceId) => {
    if (socketRef.current && isConnected) {
      socketRef.current.emit('unsubscribe-race', raceId);
    }
  };

  // Request driver metrics
  const requestMetrics = (driverId, raceId) => {
    if (socketRef.current && isConnected) {
      socketRef.current.emit('request-metrics', { driverId, raceId });
    }
  };

  // Manual reconnect
  const reconnect = () => {
    if (socketRef.current) {
      reconnectAttempts.current = 0;
      socketRef.current.connect();
    }
  };

  return {
    socket: socketRef.current,
    isConnected,
    updates: updates || [],
    latestUpdate,
    error,
    subscribeRace,
    unsubscribeRace,
    requestMetrics,
    reconnect
  };
}

