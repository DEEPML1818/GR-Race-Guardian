'use client';

import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import DriverRadarChart from './RadarChart';

export default function MultiDriverComparison({ drivers, driverTwins, liveData }) {
  const [selectedDrivers, setSelectedDrivers] = useState([]);
  const [lapDeltas, setLapDeltas] = useState([]);
  const [comparisonData, setComparisonData] = useState(null);

  useEffect(() => {
    if (drivers && drivers.length >= 2) {
      setSelectedDrivers(drivers.slice(0, 2).map(d => d.id || d.driver_id));
    }
  }, [drivers]);

  useEffect(() => {
    if (liveData?.liveData && selectedDrivers.length === 2) {
      // Calculate lap-by-lap deltas
      const deltas = [];
      const driver1Laps = liveData.liveData.lap_times?.slice(0, 20) || [];
      const driver2Laps = liveData.liveData.lap_times?.slice(0, 20) || [];
      
      const maxLaps = Math.max(driver1Laps.length, driver2Laps.length);
      for (let i = 0; i < maxLaps; i++) {
        if (driver1Laps[i] && driver2Laps[i]) {
          deltas.push({
            lap: i + 1,
            delta: (driver1Laps[i] - driver2Laps[i]).toFixed(3),
            driver1: driver1Laps[i],
            driver2: driver2Laps[i]
          });
        }
      }
      setLapDeltas(deltas);
    }
  }, [liveData, selectedDrivers]);

  if (!drivers || drivers.length < 2) {
    return (
      <div style={{ padding: 20, textAlign: 'center', color: '#999' }}>
        Need at least 2 drivers for comparison
      </div>
    );
  }

  const driver1 = drivers.find(d => (d.id || d.driver_id) === selectedDrivers[0]);
  const driver2 = drivers.find(d => (d.id || d.driver_id) === selectedDrivers[1]);
  const twin1 = driverTwins?.[selectedDrivers[0]];
  const twin2 = driverTwins?.[selectedDrivers[1]];

  return (
    <div style={{
      border: '2px solid #ddd',
      borderRadius: 8,
      padding: 20,
      backgroundColor: 'white',
      marginBottom: 20
    }}>
      <h2 style={{ marginTop: 0, color: '#333', marginBottom: 20 }}>⚖️ Multi-Driver Comparison</h2>

      {/* Driver Selector */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: '14px', color: '#666', marginBottom: 10 }}>Select Drivers to Compare:</div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {drivers.map((driver, idx) => {
            const isSelected = selectedDrivers.includes(driver.id || driver.driver_id);
            return (
              <button
                key={idx}
                onClick={() => {
                  if (selectedDrivers.length < 2 || isSelected) {
                    if (isSelected) {
                      setSelectedDrivers(selectedDrivers.filter(id => id !== (driver.id || driver.driver_id)));
                    } else {
                      setSelectedDrivers([...selectedDrivers, driver.id || driver.driver_id].slice(0, 2));
                    }
                  }
                }}
                style={{
                  padding: '8px 16px',
                  border: `2px solid ${isSelected ? '#4CAF50' : '#ddd'}`,
                  borderRadius: 6,
                  backgroundColor: isSelected ? '#e8f5e9' : 'white',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                {driver.id || driver.driver_id || `Driver ${idx + 1}`}
              </button>
            );
          })}
        </div>
      </div>

      {selectedDrivers.length === 2 && (
        <>
          {/* Radar Chart Comparison */}
          <div style={{ marginBottom: 30 }}>
            <DriverRadarChart 
              drivers={[driver1, driver2].filter(Boolean)} 
              driverTwins={driverTwins || {}}
            />
          </div>

          {/* Lap-by-Lap Delta Graph */}
          {lapDeltas.length > 0 && (
            <div style={{ marginBottom: 30 }}>
              <h3 style={{ color: '#666', fontSize: '16px', marginBottom: 15 }}>📈 Lap-by-Lap Delta</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={lapDeltas}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="lap" label={{ value: 'Lap', position: 'insideBottom' }} />
                  <YAxis label={{ value: 'Delta (s)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="delta" 
                    stroke="#8884d8" 
                    strokeWidth={2}
                    name="Delta (Driver 1 - Driver 2)"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="driver1" 
                    stroke="#82ca9d" 
                    strokeWidth={1}
                    name={driver1?.id || 'Driver 1'}
                    strokeDasharray="5 5"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="driver2" 
                    stroke="#ffc658" 
                    strokeWidth={1}
                    name={driver2?.id || 'Driver 2'}
                    strokeDasharray="5 5"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Twin vs Twin Comparison */}
          {twin1 && twin2 && (
            <div style={{ marginTop: 20, padding: 15, backgroundColor: '#f5f5f5', borderRadius: 6 }}>
              <h3 style={{ color: '#333', fontSize: '16px', marginBottom: 15 }}>🔬 Twin vs Twin Analysis</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 20 }}>
                <div>
                  <h4 style={{ color: '#4CAF50', marginBottom: 10 }}>
                    {driver1?.id || 'Driver 1'}
                  </h4>
                  <div style={{ fontSize: '14px', lineHeight: '1.8' }}>
                    <div><strong>Pace Vector:</strong> {twin1.pace_vector?.toFixed(4) || 'N/A'}</div>
                    <div><strong>Consistency:</strong> {((twin1.consistency_index || 0) * 100).toFixed(1)}%</div>
                    <div><strong>Aggression:</strong> {twin1.aggression_score?.toFixed(2) || 'N/A'}</div>
                    <div><strong>Confidence:</strong> {((twin1.confidence || 0) * 100).toFixed(1)}%</div>
                  </div>
                </div>
                <div>
                  <h4 style={{ color: '#ff9800', marginBottom: 10 }}>
                    {driver2?.id || 'Driver 2'}
                  </h4>
                  <div style={{ fontSize: '14px', lineHeight: '1.8' }}>
                    <div><strong>Pace Vector:</strong> {twin2.pace_vector?.toFixed(4) || 'N/A'}</div>
                    <div><strong>Consistency:</strong> {((twin2.consistency_index || 0) * 100).toFixed(1)}%</div>
                    <div><strong>Aggression:</strong> {twin2.aggression_score?.toFixed(2) || 'N/A'}</div>
                    <div><strong>Confidence:</strong> {((twin2.confidence || 0) * 100).toFixed(1)}%</div>
                  </div>
                </div>
              </div>

              {/* Direct Comparison */}
              <div style={{ marginTop: 20, padding: 15, backgroundColor: 'white', borderRadius: 4 }}>
                <h4 style={{ marginBottom: 10 }}>Direct Comparison</h4>
                <div style={{ fontSize: '14px' }}>
                  <div style={{ marginBottom: 5 }}>
                    <strong>Pace Advantage:</strong>{' '}
                    {twin1.pace_vector > twin2.pace_vector 
                      ? `${driver1?.id || 'Driver 1'} is faster by ${((twin1.pace_vector - twin2.pace_vector) * 1000).toFixed(2)}ms`
                      : `${driver2?.id || 'Driver 2'} is faster by ${((twin2.pace_vector - twin1.pace_vector) * 1000).toFixed(2)}ms`}
                  </div>
                  <div style={{ marginBottom: 5 }}>
                    <strong>Consistency Advantage:</strong>{' '}
                    {twin1.consistency_index > twin2.consistency_index
                      ? `${driver1?.id || 'Driver 1'} is more consistent`
                      : `${driver2?.id || 'Driver 2'} is more consistent`}
                  </div>
                  <div>
                    <strong>Overall Assessment:</strong>{' '}
                    {twin1.pace_vector > twin2.pace_vector && twin1.consistency_index > twin2.consistency_index
                      ? `${driver1?.id || 'Driver 1'} has overall advantage`
                      : twin2.pace_vector > twin1.pace_vector && twin2.consistency_index > twin1.consistency_index
                      ? `${driver2?.id || 'Driver 2'} has overall advantage`
                      : 'Drivers are closely matched'}
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
