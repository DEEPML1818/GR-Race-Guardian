import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function DeltaChart({ data }) {
  if (!data || data.length === 0) {
    return <div>No delta data available</div>;
  }

  // Transform data for delta chart
  const chartData = data.map(update => ({
    lap: update.lap,
    ...update.drivers.reduce((acc, driver, idx) => {
      acc[`Driver ${idx + 1}`] = driver.deltaToLeader || 0;
      return acc;
    }, {})
  }));

  return (
    <div style={{ width: '100%', height: 400 }}>
      <h3 style={{ marginBottom: 20 }}>Delta to Leader</h3>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="lap" label={{ value: 'Lap Number', position: 'insideBottom', offset: -5 }} />
          <YAxis label={{ value: 'Delta (seconds)', angle: -90, position: 'insideLeft' }} />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="Driver 1" stroke="#8884d8" strokeWidth={2} />
          <Line type="monotone" dataKey="Driver 2" stroke="#82ca9d" strokeWidth={2} />
          <Line type="monotone" dataKey="Driver 3" stroke="#ffc658" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

