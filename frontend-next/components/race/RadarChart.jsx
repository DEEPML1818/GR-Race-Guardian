'use client';

import { useState, useEffect } from 'react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Legend } from 'recharts';

export default function DriverRadarChart({ drivers, driverTwins }) {
  const [chartData, setChartData] = useState([]);

  useEffect(() => {
    if (drivers && driverTwins) {
      const data = drivers.map((driver, idx) => {
        const twin = driverTwins[driver.id] || driverTwins[driver.driver_id];
        if (!twin) return null;

        return {
          driver: driver.id || driver.driver_id || `Driver ${idx + 1}`,
          Pace: Math.min(100, (twin.pace_vector || 0) * 1000 + 50), // Normalize to 0-100
          Consistency: (twin.consistency_index || 0.7) * 100,
          Aggression: (twin.aggression_score || 0.5) * 100,
          'Sector 1': (twin.sector_strengths?.S1 || 1.0) * 50,
          'Sector 2': (twin.sector_strengths?.S2 || 1.0) * 50,
          'Sector 3': (twin.sector_strengths?.S3 || 1.0) * 50
        };
      }).filter(Boolean);

      setChartData(data);
    }
  }, [drivers, driverTwins]);

  if (!chartData || chartData.length === 0) {
    return (
      <div style={{
        border: '2px solid #ddd',
        borderRadius: 8,
        padding: 20,
        backgroundColor: 'white',
        textAlign: 'center',
        color: '#999'
      }}>
        No driver data available for radar chart
      </div>
    );
  }

  const colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff00'];

  return (
    <div style={{
      border: '2px solid #ddd',
      borderRadius: 8,
      padding: 20,
      backgroundColor: 'white',
      marginBottom: 20
    }}>
      <h2 style={{ marginTop: 0, color: '#333', marginBottom: 20 }}>📊 Driver Comparison Radar</h2>
      
      <ResponsiveContainer width="100%" height={400}>
        <RadarChart data={chartData}>
          <PolarGrid />
          <PolarAngleAxis dataKey="driver" />
          <PolarRadiusAxis angle={90} domain={[0, 100]} />
          {chartData.map((_, idx) => (
            <Radar
              key={idx}
              name={chartData[idx].driver}
              dataKey={chartData[idx].driver}
              stroke={colors[idx % colors.length]}
              fill={colors[idx % colors.length]}
              fillOpacity={0.6}
            />
          ))}
          <Legend />
        </RadarChart>
      </ResponsiveContainer>

      {/* Metrics Legend */}
      <div style={{ marginTop: 20, padding: 15, backgroundColor: '#f5f5f5', borderRadius: 6 }}>
        <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: 10 }}>Metrics:</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, fontSize: '12px' }}>
          <div><strong>Pace:</strong> Normalized pace vector (0-100)</div>
          <div><strong>Consistency:</strong> Lap-to-lap consistency (0-100%)</div>
          <div><strong>Aggression:</strong> Driving aggression score (0-100)</div>
          <div><strong>Sector 1:</strong> Sector 1 strength (0-100)</div>
          <div><strong>Sector 2:</strong> Sector 2 strength (0-100)</div>
          <div><strong>Sector 3:</strong> Sector 3 strength (0-100)</div>
        </div>
      </div>
    </div>
  );
}

