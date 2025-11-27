'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

export default function TrafficMap({ drivers, currentLap, sector }) {
  const [trafficDensity, setTrafficDensity] = useState({ S1: 0.3, S2: 0.5, S3: 0.2 });
  const [selectedSector, setSelectedSector] = useState(sector || 'S1');

  useEffect(() => {
    if (drivers && drivers.length > 0) {
      // Calculate traffic density per sector
      const density = { S1: 0, S2: 0, S3: 0 };
      drivers.forEach(driver => {
        const sector = driver.sector || 'S1';
        if (density[sector] !== undefined) {
          density[sector] += 1;
        }
      });
      
      // Normalize
      const total = drivers.length;
      Object.keys(density).forEach(s => {
        density[s] = total > 0 ? density[s] / total : 0;
      });
      
      setTrafficDensity(density);
    }
  }, [drivers]);

  const getTrafficColor = (density) => {
    if (density > 0.7) return '#f44336'; // Red - Heavy traffic
    if (density > 0.4) return '#ff9800'; // Orange - Moderate traffic
    return '#4CAF50'; // Green - Clear
  };

  const getTrafficLabel = (density) => {
    if (density > 0.7) return 'Heavy Traffic';
    if (density > 0.4) return 'Moderate Traffic';
    return 'Clear';
  };

  return (
    <div style={{ 
      border: '2px solid #ddd', 
      borderRadius: 8, 
      padding: 20,
      backgroundColor: 'white',
      marginBottom: 20
    }}>
      <h2 style={{ marginTop: 0, color: '#333' }}>🚦 Traffic Rejoin Map</h2>
      
      {/* Sector Traffic Display */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 15, marginBottom: 20 }}>
        {['S1', 'S2', 'S3'].map((sector) => {
          const density = trafficDensity[sector] || 0;
          const color = getTrafficColor(density);
          
          return (
            <motion.div
              key={sector}
              whileHover={{ scale: 1.05 }}
              onClick={() => setSelectedSector(sector)}
              style={{
                border: selectedSector === sector ? `3px solid ${color}` : `2px solid ${color}`,
                borderRadius: 8,
                padding: 20,
                backgroundColor: color + '20',
                cursor: 'pointer',
                textAlign: 'center'
              }}
            >
              <div style={{ fontSize: '24px', fontWeight: 'bold', color }}>{sector}</div>
              <div style={{ fontSize: '18px', marginTop: 5, color: '#666' }}>
                {getTrafficLabel(density)}
              </div>
              <div style={{ fontSize: '14px', marginTop: 5, color: '#666' }}>
                {(density * 100).toFixed(0)}% density
              </div>
              {drivers && (
                <div style={{ fontSize: '12px', marginTop: 5, color: '#999' }}>
                  {drivers.filter(d => d.sector === sector).length} drivers
                </div>
              )}
            </motion.div>
          );
        })}
      </div>

      {/* Driver Positions in Selected Sector */}
      {drivers && drivers.length > 0 && (
        <div>
          <h3 style={{ color: '#666', fontSize: '16px' }}>Drivers in {selectedSector}</h3>
          <div style={{ 
            display: 'flex', 
            gap: 10, 
            flexWrap: 'wrap',
            marginTop: 10
          }}>
            {drivers
              .filter(d => d.sector === selectedSector)
              .sort((a, b) => (a.position || 0) - (b.position || 0))
              .map((driver, idx) => (
                <div
                  key={idx}
                  style={{
                    border: '1px solid #ddd',
                    borderRadius: 6,
                    padding: 10,
                    backgroundColor: '#fafafa',
                    minWidth: 100,
                    textAlign: 'center'
                  }}
                >
                  <div style={{ fontWeight: 'bold', fontSize: '14px' }}>
                    {driver.id || `Driver ${idx + 1}`}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    P{driver.position || idx + 1}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    {driver.lapTime?.toFixed(3) || 'N/A'}s
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Track Visualization */}
      <div style={{ marginTop: 20, padding: 15, backgroundColor: '#f5f5f5', borderRadius: 6 }}>
        <h3 style={{ color: '#333', fontSize: '16px', marginBottom: 10 }}>📍 Track Map</h3>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-around', 
          alignItems: 'center',
          padding: 20,
          backgroundColor: 'white',
          borderRadius: 4,
          position: 'relative',
          minHeight: 150
        }}>
          {['S1', 'S2', 'S3'].map((sector, idx) => {
            const density = trafficDensity[sector] || 0;
            const color = density > 0.7 ? '#f44336' : density > 0.4 ? '#ff9800' : '#4CAF50';
            const driversInSector = drivers?.filter(d => d.sector === sector).length || 0;
            
            return (
              <div
                key={sector}
                style={{
                  flex: 1,
                  textAlign: 'center',
                  padding: 15,
                  border: `3px solid ${color}`,
                  borderRadius: 8,
                  backgroundColor: color + '20',
                  margin: '0 5px',
                  position: 'relative'
                }}
              >
                <div style={{ fontSize: '24px', fontWeight: 'bold', color }}>{sector}</div>
                <div style={{ fontSize: '12px', marginTop: 5, color: '#666' }}>
                  {driversInSector} driver{driversInSector !== 1 ? 's' : ''}
                </div>
                <div style={{ 
                  position: 'absolute', 
                  top: 5, 
                  right: 5, 
                  width: 10, 
                  height: 10, 
                  borderRadius: '50%', 
                  backgroundColor: color 
                }} />
              </div>
            );
          })}
        </div>
      </div>

      {/* Traffic Density Heatmap */}
      <div style={{ marginTop: 20 }}>
        <h3 style={{ color: '#333', fontSize: '16px', marginBottom: 10 }}>🔥 Traffic Density Heatmap</h3>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          {['S1', 'S2', 'S3'].map((sector) => {
            const density = trafficDensity[sector] || 0;
            const intensity = Math.floor(density * 100);
            const color = density > 0.7 ? '#f44336' : density > 0.4 ? '#ff9800' : '#4CAF50';
            
            return (
              <div key={sector} style={{ flex: 1, textAlign: 'center' }}>
                <div style={{
                  height: 100,
                  backgroundColor: color,
                  opacity: density,
                  borderRadius: 4,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  fontWeight: 'bold',
                  fontSize: '18px'
                }}>
                  {intensity}%
                </div>
                <div style={{ marginTop: 5, fontSize: '12px' }}>{sector}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Pit Rejoin Ghost Path */}
      {drivers && drivers.length > 0 && (
        <div style={{ marginTop: 20, padding: 15, backgroundColor: '#e3f2fd', borderRadius: 6 }}>
          <h3 style={{ color: '#1976d2', fontSize: '16px', marginBottom: 10 }}>👻 Pit Rejoin Ghost Path</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 10, fontSize: '14px' }}>
            <div>
              <strong>Current Position:</strong> P{drivers[0]?.position || 'N/A'}
            </div>
            <div>
              <strong>Rejoin Position:</strong> P{Math.min((drivers[0]?.position || 1) + 2, 20)}
            </div>
            <div>
              <strong>Traffic Impact:</strong> {trafficDensity[selectedSector] > 0.5 ? 'High' : 'Low'}
            </div>
            <div>
              <strong>Clear Window:</strong> {trafficDensity[selectedSector] < 0.4 ? '✅ Yes' : '❌ No'}
            </div>
            <div>
              <strong>Time Lost:</strong> {(trafficDensity[selectedSector] * 2).toFixed(2)}s
            </div>
            <div>
              <strong>Ghost Position:</strong> P{drivers[0]?.position || 'N/A'} (without pit)
            </div>
          </div>
        </div>
      )}

      {/* Traffic Density Legend */}
      <div style={{ marginTop: 20, padding: 10, backgroundColor: '#f5f5f5', borderRadius: 6 }}>
        <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: 5 }}>Traffic Density Legend:</div>
        <div style={{ display: 'flex', gap: 15, fontSize: '12px' }}>
          <div><span style={{ color: '#4CAF50' }}>●</span> Clear (&lt;40%)</div>
          <div><span style={{ color: '#ff9800' }}>●</span> Moderate (40-70%)</div>
          <div><span style={{ color: '#f44336' }}>●</span> Heavy (&gt;70%)</div>
        </div>
      </div>
    </div>
  );
}

