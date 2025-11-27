'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';

export default function PitDecisionPanel({ raceId, driverId, currentLap, tireAge }) {
  const [decision, setDecision] = useState(null);
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    if (raceId && currentLap) {
      fetchPitDecision();
      
      // Refresh every 5 seconds
      const interval = setInterval(() => {
        fetchPitDecision();
      }, 5000);
      
      return () => clearInterval(interval);
    }
  }, [raceId, driverId, currentLap, tireAge]);

  const fetchPitDecision = async () => {
    setLoading(true);
    try {
      const response = await axios.post('http://localhost:3001/api/ai/pit-decision', {
        race_twin: {
          degradation_curve: {
            critical: tireAge > 20,
            trend: tireAge > 15 ? 'increasing' : 'stable'
          },
          traffic_simulation: {
            clear_window: currentLap % 3 !== 0, // Simulate clear windows
            busy: currentLap % 3 === 0
          },
          tire_age: tireAge || 10,
          undercut_outcomes: {
            viable: tireAge > 15,
            time_gain: tireAge > 15 ? 2.5 : 0
          }
        },
        lap_data: [{ lap: currentLap, lap_time: 95.234 }]
      });

      if (response.data.analysis) {
        setDecision(response.data.analysis);
        setLastUpdate(new Date());
      }
    } catch (error) {
      console.error('Failed to fetch pit decision:', error);
    } finally {
      setLoading(false);
    }
  };

  const getDecisionColor = (decisionType) => {
    switch (decisionType) {
      case 'PIT_NOW':
        return { bg: '#fff3cd', border: '#ffc107', text: '#856404' };
      case 'PIT_LATER':
        return { bg: '#d1ecf1', border: '#17a2b8', text: '#0c5460' };
      case 'EXTEND_STINT':
        return { bg: '#f8d7da', border: '#dc3545', text: '#721c24' };
      default:
        return { bg: '#e2e3e5', border: '#6c757d', text: '#383d41' };
    }
  };

  const getDecisionIcon = (decisionType) => {
    switch (decisionType) {
      case 'PIT_NOW':
        return '🚨';
      case 'PIT_LATER':
        return '⏱️';
      case 'EXTEND_STINT':
        return '🔄';
      default:
        return '📊';
    }
  };

  if (loading && !decision) {
    return (
      <div style={{ padding: 20, textAlign: 'center' }}>
        Analyzing pit decision...
      </div>
    );
  }

  if (!decision) {
    return null;
  }

  const colors = getDecisionColor(decision.decision);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        border: `3px solid ${colors.border}`,
        borderRadius: 8,
        padding: 20,
        backgroundColor: colors.bg,
        marginBottom: 20
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15 }}>
        <h2 style={{ margin: 0, color: colors.text, display: 'flex', alignItems: 'center', gap: 10 }}>
          {getDecisionIcon(decision.decision)} Live Pit Decision
        </h2>
        {lastUpdate && (
          <span style={{ fontSize: '12px', color: '#666' }}>
            Updated: {lastUpdate.toLocaleTimeString()}
          </span>
        )}
      </div>

      {/* Decision Display */}
      <div style={{
        textAlign: 'center',
        padding: 20,
        backgroundColor: 'white',
        borderRadius: 6,
        marginBottom: 15
      }}>
        <div style={{ fontSize: '32px', fontWeight: 'bold', color: colors.border, marginBottom: 10 }}>
          {decision.decision}
        </div>
        <div style={{ fontSize: '18px', color: '#666' }}>
          Confidence: <strong style={{ color: colors.border }}>{decision.confidence?.toUpperCase() || 'MEDIUM'}</strong>
        </div>
      </div>

      {/* Reasoning */}
      {decision.reasoning && (
        <div style={{ marginBottom: 15 }}>
          <h3 style={{ color: colors.text, fontSize: '16px', marginBottom: 10 }}>📋 Analysis:</h3>
          {Array.isArray(decision.reasoning) && decision.reasoning.length > 0 ? (
            <ul style={{ paddingLeft: 20, margin: 0 }}>
              {decision.reasoning.map((reason, idx) => (
                <li key={idx} style={{ color: '#666', marginBottom: 5 }}>{reason}</li>
              ))}
            </ul>
          ) : typeof decision.reasoning === 'string' ? (
            <div style={{ color: '#666' }}>{decision.reasoning}</div>
          ) : null}
        </div>
      )}

      {/* Factors */}
      {decision.factors && (
        <div style={{ marginTop: 15, padding: 15, backgroundColor: 'white', borderRadius: 6 }}>
          <h3 style={{ color: '#666', fontSize: '16px', marginBottom: 10 }}>📊 Evaluated Factors:</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 10, fontSize: '14px' }}>
            {decision.factors.degradation && (
              <div>
                <strong>Degradation:</strong> {decision.factors.degradation.critical ? 'Critical' : 'Normal'}
              </div>
            )}
            {decision.factors.traffic_window && (
              <div>
                <strong>Traffic:</strong> {decision.factors.traffic_window.clear ? 'Clear Window' : 'Heavy Traffic'}
              </div>
            )}
            {decision.factors.tire_age && (
              <div>
                <strong>Tire Age:</strong> {decision.factors.tire_age.age || tireAge || 'N/A'} laps
                {decision.factors.tire_age.critical && ' (Critical!)'}
              </div>
            )}
            {decision.factors.undercut_viability && (
              <div>
                <strong>Undercut:</strong> {decision.factors.undercut_viability.viable ? 'Viable' : 'Not Viable'}
                {decision.factors.undercut_viability.advantage > 0 && 
                  ` (+${decision.factors.undercut_viability.advantage.toFixed(1)}s)`}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Confidence Bar */}
      <div style={{ marginTop: 15 }}>
        <div style={{ fontSize: '14px', color: '#666', marginBottom: 5 }}>
          Confidence Level:
        </div>
        <div style={{ 
          width: '100%', 
          height: 20, 
          backgroundColor: '#e0e0e0', 
          borderRadius: 10,
          overflow: 'hidden'
        }}>
          <motion.div
            initial={{ width: 0 }}
            animate={{ 
              width: decision.confidence === 'high' ? '90%' : 
                     decision.confidence === 'medium' ? '60%' : '30%'
            }}
            transition={{ duration: 0.5 }}
            style={{
              height: '100%',
              backgroundColor: decision.confidence === 'high' ? '#4CAF50' :
                            decision.confidence === 'medium' ? '#ff9800' : '#f44336',
              borderRadius: 10,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontSize: '12px',
              fontWeight: 'bold'
            }}
          >
            {decision.confidence?.toUpperCase() || 'MEDIUM'}
          </motion.div>
        </div>
      </div>

      {/* Current Status */}
      <div style={{ marginTop: 15, fontSize: '14px', color: '#666', display: 'flex', justifyContent: 'space-between' }}>
        <div>Current Lap: <strong>{currentLap || 'N/A'}</strong></div>
        <div>Tire Age: <strong>{tireAge || 'N/A'} laps</strong></div>
      </div>
    </motion.div>
  );
}

