'use client';

import { useState, useEffect, useRef } from 'react';

export default function RaceReplay({ replayData, trackId, onTimeChange }) {
  const [raceTime, setRaceTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(10); // Default faster speed for time-based
  const [maxTime, setMaxTime] = useState(0);
  const lastFrameTimeRef = useRef(null);
  const requestRef = useRef(null);

  // Calculate max race time from replay data
  useEffect(() => {
    if (replayData?.lap_progression?.length > 0) {
      const lastLap = replayData.lap_progression[replayData.lap_progression.length - 1];
      if (lastLap?.positions?.length > 0) {
        // Find the maximum cumulative time in the last lap
        const maxT = Math.max(...lastLap.positions.map(p => p.cumulative_time || 0));
        setMaxTime(Math.ceil(maxT));
      }
    }
  }, [replayData]);

  // Notify parent of time change
  useEffect(() => {
    if (onTimeChange) {
      onTimeChange(raceTime);
    }
  }, [raceTime, onTimeChange]);

  // Animation loop
  const animate = (time) => {
    if (lastFrameTimeRef.current !== undefined) {
      const deltaTime = (time - lastFrameTimeRef.current) / 1000; // Convert to seconds
      
      setRaceTime(prevTime => {
        const newTime = prevTime + (deltaTime * playbackSpeed);
        if (newTime >= maxTime) {
          setIsPlaying(false);
          return maxTime;
        }
        return newTime;
      });
    }
    lastFrameTimeRef.current = time;
    if (isPlaying) {
      requestRef.current = requestAnimationFrame(animate);
    }
  };

  useEffect(() => {
    if (isPlaying) {
      lastFrameTimeRef.current = performance.now();
      requestRef.current = requestAnimationFrame(animate);
    } else {
      if (requestRef.current) {
        cancelAnimationFrame(requestRef.current);
      }
      lastFrameTimeRef.current = undefined;
    }

    return () => {
      if (requestRef.current) {
        cancelAnimationFrame(requestRef.current);
      }
    };
  }, [isPlaying, maxTime, playbackSpeed]);

  const handlePlay = () => {
    if (raceTime >= maxTime) {
      setRaceTime(0);
    }
    setIsPlaying(true);
  };

  const handlePause = () => {
    setIsPlaying(false);
  };

  const handleReset = () => {
    setIsPlaying(false);
    setRaceTime(0);
  };

  const handleTimeChange = (time) => {
    setIsPlaying(false);
    setRaceTime(Math.max(0, Math.min(time, maxTime)));
  };

  // Format time helper
  const formatTime = (seconds) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${h > 0 ? h + ':' : ''}${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  if (!replayData || !replayData.lap_progression) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#999' }}>
        Race replay data not available
      </div>
    );
  }

  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: '8px',
      padding: '20px',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }}>
      <h2 style={{ fontSize: '20px', marginBottom: '15px', color: '#333' }}>
        Race Replay
      </h2>

      {/* Controls */}
      <div style={{
        display: 'flex',
        gap: '10px',
        marginBottom: '20px',
        alignItems: 'center',
        flexWrap: 'wrap'
      }}>
        <button
          onClick={isPlaying ? handlePause : handlePlay}
          style={{
            padding: '10px 20px',
            backgroundColor: isPlaying ? '#f44336' : '#4CAF50',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: 'bold'
          }}
        >
          {isPlaying ? '⏸ Pause' : '▶ Play'}
        </button>
        
        <button
          onClick={handleReset}
          style={{
            padding: '10px 20px',
            backgroundColor: '#666',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          ⏮ Reset
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <label style={{ fontSize: '14px', color: '#666' }}>Speed:</label>
          <select
            value={playbackSpeed}
            onChange={(e) => setPlaybackSpeed(parseFloat(e.target.value))}
            style={{
              padding: '5px 10px',
              borderRadius: '4px',
              border: '1px solid #ddd',
              fontSize: '14px'
            }}
          >
            <option value="1">1x (Real-time)</option>
            <option value="10">10x</option>
            <option value="50">50x</option>
            <option value="100">100x</option>
            <option value="500">500x</option>
          </select>
        </div>

        <div style={{ marginLeft: 'auto', fontSize: '14px', color: '#666', fontFamily: 'monospace' }}>
          {formatTime(raceTime)} / {formatTime(maxTime)}
        </div>
      </div>

      {/* Time Slider */}
      <div style={{ marginBottom: '20px' }}>
        <input
          type="range"
          min="0"
          max={maxTime}
          step="0.1"
          value={raceTime}
          onChange={(e) => handleTimeChange(parseFloat(e.target.value))}
          style={{
            width: '100%',
            height: '6px',
            borderRadius: '3px',
            outline: 'none'
          }}
        />
      </div>

      {/* Race Summary */}
      {replayData.results && replayData.results.length > 0 && (
        <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#f9f9f9', borderRadius: '6px' }}>
          <h3 style={{ fontSize: '16px', marginBottom: '10px', color: '#333' }}>
            Race Summary
          </h3>
          <div style={{ fontSize: '14px', color: '#666' }}>
            <p><strong>Winner:</strong> #{replayData.results[0]?.vehicle_number || 'N/A'} - {replayData.results[0]?.total_time || 'N/A'}</p>
            <p><strong>Total Drivers:</strong> {replayData.results.length || replayData.total_drivers || 0}</p>
            <p><strong>Total Laps:</strong> {replayData.total_laps || 0}</p>
          </div>
        </div>
      )}
    </div>
  );
}

