'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';

// Dynamically import Plotly with SSR disabled
const Plot = dynamic(
  () => import('react-plotly.js'),
  { 
    ssr: false,
    loading: () => <div>Loading telemetry graph...</div>
  }
);

export default function TelemetryGraph({ telemetryData }) {
  const [isClient, setIsClient] = useState(false);

  // Only render on client side
  useEffect(() => {
    setIsClient(true);
  }, []);

  if (!isClient) {
    return <div>Loading telemetry graph...</div>;
  }

  if (!telemetryData || telemetryData.length === 0) {
    return (
      <div style={{ padding: 20, textAlign: 'center', color: '#666' }}>
        No telemetry data available
      </div>
    );
  }

  // Sample telemetry data structure
  const traces = [
    {
      x: telemetryData.map((_, idx) => idx),
      y: telemetryData.map(d => d.speed || 0),
      type: 'scatter',
      mode: 'lines',
      name: 'Speed (km/h)',
      line: { color: '#1f77b4' }
    },
    {
      x: telemetryData.map((_, idx) => idx),
      y: telemetryData.map(d => d.throttle || 0),
      type: 'scatter',
      mode: 'lines',
      name: 'Throttle (%)',
      line: { color: '#ff7f0e' },
      yaxis: 'y2'
    },
    {
      x: telemetryData.map((_, idx) => idx),
      y: telemetryData.map(d => d.brake || 0),
      type: 'scatter',
      mode: 'lines',
      name: 'Brake (%)',
      line: { color: '#d62728' },
      yaxis: 'y2'
    }
  ];

  return (
    <div style={{ width: '100%', height: 500 }}>
      <h3 style={{ marginBottom: 20 }}>Telemetry Data</h3>
      <Plot
        data={traces}
        layout={{
          title: 'Speed, Throttle, and Brake',
          xaxis: { title: 'Sample' },
          yaxis: { title: 'Speed (km/h)', side: 'left' },
          yaxis2: {
            title: 'Throttle/Brake (%)',
            side: 'right',
            overlaying: 'y'
          },
          height: 500,
          autosize: true,
          hovermode: 'closest'
        }}
        style={{ width: '100%', height: '100%' }}
        useResizeHandler={true}
        config={{ responsive: true }}
      />
    </div>
  );
}
