'use client';

import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import axios from 'axios';

export default function StrategyConsole({ raceId, driverId }) {
  const [strategy, setStrategy] = useState(null);
  const [pitWindows, setPitWindows] = useState([]);
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(false);

  // Fetch strategy data
  useEffect(() => {
    if (raceId) {
      fetchStrategy(raceId);
    }
  }, [raceId, driverId]);

  const fetchStrategy = async (raceId) => {
    setLoading(true);
    try {
      // Fetch pit window recommendations
      const pitWindowRes = await axios.post('http://localhost:3001/api/ai/pit-decision', {
        race_twin: {
          degradation_curve: { critical: false, trend: 'increasing' },
          traffic_simulation: { clear_window: true },
          tire_age: 15
        }
      });

      if (pitWindowRes.data.analysis) {
        setRecommendations(pitWindowRes.data.analysis);
      }

      // Simulate pit strategy data
      const simulatedStrategy = {
        recommendedPits: [18, 38],
        tireCompounds: ['SOFT', 'MEDIUM', 'HARD'],
        estimatedGains: [2.5, 1.8],
        risks: ['Traffic at lap 19', 'Undercut opportunity at lap 17']
      };
      setStrategy(simulatedStrategy);

      // Generate pit windows chart data
      const windows = [];
      for (let i = 0; i < 3; i++) {
        windows.push({
          stint: `Stint ${i + 1}`,
          startLap: i * 20,
          endLap: (i + 1) * 20,
          compound: ['SOFT', 'MEDIUM', 'HARD'][i],
          degradation: 0.5 + i * 0.3
        });
      }
      setPitWindows(windows);

    } catch (error) {
      console.error('Failed to fetch strategy:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Loading strategy...</div>;
  }

  return (
    <div style={{ 
      border: '2px solid #ddd', 
      borderRadius: 8, 
      padding: 20,
      backgroundColor: 'white',
      marginBottom: 20
    }}>
      <h2 style={{ marginTop: 0, color: '#333' }}>🎯 Strategy Console</h2>
      
      {/* Recommended Pit Windows */}
      {strategy && (
        <div style={{ marginBottom: 20 }}>
          <h3 style={{ color: '#666', fontSize: '16px' }}>Recommended Pit Windows</h3>
          <div style={{ display: 'flex', gap: 15, flexWrap: 'wrap' }}>
            {strategy.recommendedPits.map((lap, idx) => (
              <div 
                key={idx}
                style={{
                  border: '2px solid #4CAF50',
                  borderRadius: 6,
                  padding: 15,
                  backgroundColor: '#f0f8f0',
                  minWidth: 150
                }}
              >
                <div style={{ fontWeight: 'bold', color: '#4CAF50' }}>Pit Window {idx + 1}</div>
                <div style={{ fontSize: '24px', fontWeight: 'bold' }}>Lap {lap}</div>
                <div style={{ fontSize: '14px', color: '#666' }}>
                  Compound: {strategy.tireCompounds[idx] || 'MEDIUM'}
                </div>
                <div style={{ fontSize: '14px', color: '#666' }}>
                  Est. Gain: {strategy.estimatedGains[idx]?.toFixed(2) || 'N/A'}s
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Pit Decision Recommendation */}
      {recommendations && (
        <div style={{ 
          marginBottom: 20,
          padding: 15,
          backgroundColor: recommendations.decision === 'PIT_NOW' ? '#fff3cd' : 
                          recommendations.decision === 'PIT_LATER' ? '#d1ecf1' : '#f8d7da',
          borderRadius: 6,
          border: `2px solid ${recommendations.decision === 'PIT_NOW' ? '#ffc107' : 
                                      recommendations.decision === 'PIT_LATER' ? '#17a2b8' : '#dc3545'}`
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <h3 style={{ margin: 0, fontSize: '18px' }}>AI Pit Decision</h3>
            <span style={{ 
              padding: '5px 10px',
              backgroundColor: recommendations.decision === 'PIT_NOW' ? '#ffc107' : 
                              recommendations.decision === 'PIT_LATER' ? '#17a2b8' : '#dc3545',
              color: 'white',
              borderRadius: 4,
              fontWeight: 'bold'
            }}>
              {recommendations.decision}
            </span>
          </div>
          <div style={{ fontSize: '14px', marginBottom: 10 }}>
            <strong>Confidence:</strong> {recommendations.confidence || 'medium'}
          </div>
          <div style={{ fontSize: '14px' }}>
            <strong>Reasoning:</strong>
            <ul style={{ margin: '5px 0', paddingLeft: 20 }}>
              {recommendations.reasoning && recommendations.reasoning.map((reason, idx) => (
                <li key={idx}>{reason}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Strategy Risks */}
      {strategy?.risks && strategy.risks.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <h3 style={{ color: '#f44336', fontSize: '16px' }}>⚠️ Strategy Risks</h3>
          <ul style={{ paddingLeft: 20 }}>
            {strategy.risks.map((risk, idx) => (
              <li key={idx} style={{ color: '#666', marginBottom: 5 }}>{risk}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Tire Degradation Graph */}
      <div style={{ marginTop: 20 }}>
        <h3 style={{ color: '#666', fontSize: '16px' }}>Tire Degradation Projection</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={pitWindows.map((w, idx) => ({ lap: w.startLap, degradation: w.degradation }))}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="lap" label={{ value: 'Lap', position: 'insideBottom' }} />
            <YAxis label={{ value: 'Degradation', angle: -90, position: 'insideLeft' }} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="degradation" stroke="#f44336" strokeWidth={2} name="Degradation Rate" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Undercut/Overtake Simulator */}
      <div style={{ marginTop: 20, padding: 15, backgroundColor: '#e3f2fd', borderRadius: 6 }}>
        <h3 style={{ color: '#1976d2', fontSize: '16px', marginBottom: 10 }}>🎯 Undercut/Overtake Analysis</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 15 }}>
          <div style={{ padding: 10, backgroundColor: 'white', borderRadius: 4 }}>
            <div style={{ fontWeight: 'bold', color: '#4CAF50', marginBottom: 5 }}>Undercut Opportunity</div>
            <div style={{ fontSize: '14px' }}>Potential Gain: {strategy?.estimatedGains?.[0]?.toFixed(2) || '2.5'}s</div>
            <div style={{ fontSize: '12px', color: '#666', marginTop: 5 }}>
              Pit early to gain on fresh tires
            </div>
          </div>
          <div style={{ padding: 10, backgroundColor: 'white', borderRadius: 4 }}>
            <div style={{ fontWeight: 'bold', color: '#ff9800', marginBottom: 5 }}>Overtake Window</div>
            <div style={{ fontSize: '14px' }}>Risk Level: Medium</div>
            <div style={{ fontSize: '12px', color: '#666', marginTop: 5 }}>
              Monitor opponent tire degradation
            </div>
          </div>
        </div>
      </div>

      {/* Risk Scoring */}
      <div style={{ marginTop: 20, padding: 15, backgroundColor: '#fff3cd', borderRadius: 6 }}>
        <h3 style={{ color: '#856404', fontSize: '16px', marginBottom: 10 }}>⚠️ Strategy Risk Assessment</h3>
        <div style={{ display: 'flex', gap: 15, fontSize: '14px' }}>
          <div>
            <strong>Tire Risk:</strong> {strategy?.tireAge > 20 ? 'High' : 'Low'}
          </div>
          <div>
            <strong>Traffic Risk:</strong> Medium
          </div>
          <div>
            <strong>Timing Risk:</strong> Low
          </div>
        </div>
      </div>
    </div>
  );
}

