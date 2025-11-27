import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { useSocket } from '../hooks/useSocket';
import LapChart from '../components/LapChart';
import DeltaChart from '../components/DeltaChart';

// Dynamically import components that need SSR disabled
const TelemetryGraph = dynamic(
  () => import('../components/TelemetryGraph'),
  { ssr: false }
);

// Import advanced race components
import StrategyConsole from '../components/race/StrategyConsole';
import TrafficMap from '../components/race/TrafficMap';
import PitDecisionPanel from '../components/race/PitDecisionPanel';
import MultiDriverComparison from '../components/race/MultiDriverComparison';
import AIAgentPanel from '../components/race/AIAgentPanel';

export default function Home() {
  const [raceId] = useState(1);
  const { isConnected, updates = [], latestUpdate, requestDriverMetrics } = useSocket(raceId);
  const [raceStarted, setRaceStarted] = useState(false);
  const [stats, setStats] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard'); // dashboard, strategy, comparison
  const [currentLap, setCurrentLap] = useState(1);
  const [tireAge, setTireAge] = useState(0);

  // Navigation to tracks page
  const navigateToTracks = () => {
    window.location.href = '/tracks';
  };

  // Start/stop race simulation
  const startRace = async () => {
    try {
      const res = await fetch('http://localhost:3001/api/race/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raceId: 1 })
      });
      const data = await res.json();
      if (data.success) {
        setRaceStarted(true);
        setTireAge(0);
        setCurrentLap(1);
      }
    } catch (error) {
      console.error('Failed to start race:', error);
    }
  };

  const stopRace = async () => {
    try {
      const res = await fetch('http://localhost:3001/api/race/stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await res.json();
      if (data.success) {
        setRaceStarted(false);
      }
    } catch (error) {
      console.error('Failed to stop race:', error);
    }
  };

  // Update lap and tire age from updates
  useEffect(() => {
    if (latestUpdate) {
      setCurrentLap(latestUpdate.lap || 1);
      // Simulate tire aging (1 lap per update)
      if (latestUpdate.lap) {
        setTireAge(latestUpdate.lap - 1);
      }
    }
  }, [latestUpdate]);

  // Calculate statistics from updates
  useEffect(() => {
    if (updates && updates.length > 0 && latestUpdate) {
      const driverStats = latestUpdate.drivers?.map((driver, idx) => {
        const driverUpdates = updates.filter(u => u.drivers?.[idx]);
        const lapTimes = driverUpdates.map(u => u.drivers[idx].lapTime).filter(t => t);
        
        return {
          id: driver.id,
          currentLap: latestUpdate.lap,
          currentTime: driver.lapTime,
          position: driver.position,
          sector: driver.sector,
          deltaToLeader: driver.deltaToLeader || 0,
          avgLapTime: lapTimes.length > 0 
            ? lapTimes.reduce((a, b) => a + b, 0) / lapTimes.length
            : null,
          bestLapTime: lapTimes.length > 0 
            ? Math.min(...lapTimes)
            : null
        };
      });
      
      setStats(driverStats);
    }
  }, [updates, latestUpdate]);

  return (
    <div style={{ padding: 20, fontFamily: 'Arial, sans-serif', minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
      {/* Header */}
      <div style={{ marginBottom: 30, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ margin: 0, color: '#333' }}>🏎️ GR Race Guardian — Live Dashboard</h1>
          <p style={{ color: '#666', marginTop: 5 }}>Professional Motorsport Analytics Platform</p>
        </div>
        <button
          onClick={navigateToTracks}
          style={{
            padding: '12px 24px',
            backgroundColor: '#2196F3',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '16px',
            fontWeight: 'bold',
            boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
          }}
        >
          🗺️ View Race Tracks
        </button>
      </div>

      {/* Connection Status and Controls */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: 30,
        padding: 15,
        backgroundColor: 'white',
        borderRadius: 8,
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <div>
          <span style={{ 
            padding: '8px 16px', 
            backgroundColor: isConnected ? '#4CAF50' : '#f44336',
            color: 'white',
            borderRadius: 4,
            fontWeight: 'bold',
            fontSize: '14px'
          }}>
            {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
          </span>
          <span style={{ marginLeft: 15, color: '#666' }}>
            Updates: {updates?.length || 0} | Race ID: {raceId} | Lap: {currentLap}
          </span>
        </div>
        
        <div>
          {!raceStarted ? (
            <button 
              onClick={startRace}
              style={{
                padding: '10px 20px',
                backgroundColor: '#4CAF50',
                color: 'white',
                border: 'none',
                borderRadius: 4,
                cursor: 'pointer',
                fontWeight: 'bold',
                fontSize: '14px'
              }}
            >
              ▶️ Start Race Simulation
            </button>
          ) : (
            <button 
              onClick={stopRace}
              style={{
                padding: '10px 20px',
                backgroundColor: '#f44336',
                color: 'white',
                border: 'none',
                borderRadius: 4,
                cursor: 'pointer',
                fontWeight: 'bold',
                fontSize: '14px'
              }}
            >
              ⏹️ Stop Race
            </button>
          )}
        </div>
      </div>

      {/* Tab Navigation */}
      <div style={{ 
        display: 'flex', 
        gap: 10, 
        marginBottom: 20,
        borderBottom: '2px solid #ddd'
      }}>
        {['dashboard', 'strategy', 'comparison'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '10px 20px',
              border: 'none',
              borderBottom: activeTab === tab ? '3px solid #4CAF50' : '3px solid transparent',
              backgroundColor: 'transparent',
              cursor: 'pointer',
              fontWeight: activeTab === tab ? 'bold' : 'normal',
              color: activeTab === tab ? '#4CAF50' : '#666',
              fontSize: '14px',
              textTransform: 'capitalize'
            }}
          >
            {tab === 'dashboard' ? '📊 Dashboard' : 
             tab === 'strategy' ? '🎯 Strategy' : 
             '📈 Comparison'}
          </button>
        ))}
      </div>

      {/* Dashboard Tab */}
      {activeTab === 'dashboard' && (
        <>
          {/* Latest Update */}
          {latestUpdate && (
            <div style={{ 
              border: '2px solid #ddd', 
              padding: 20, 
              borderRadius: 8,
              marginBottom: 30,
              backgroundColor: 'white',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
            }}>
              <h2 style={{ marginTop: 0, color: '#333' }}>📊 Latest Race Update</h2>
              <p style={{ color: '#666', marginBottom: 15 }}>
                <strong>Time:</strong> {new Date(latestUpdate.timestamp).toLocaleTimeString()} | 
                <strong> Lap:</strong> {latestUpdate.lap}
              </p>
              
              {stats && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 15 }}>
                  {stats.map((driver, idx) => (
                    <div 
                      key={idx}
                      style={{
                        border: '1px solid #ddd',
                        padding: 15,
                        borderRadius: 6,
                        backgroundColor: '#fafafa'
                      }}
                    >
                      <h3 style={{ margin: '0 0 10px 0', color: '#333' }}>
                        {driver.id} - P{driver.position}
                      </h3>
                      <div style={{ fontSize: '14px', lineHeight: '1.6' }}>
                        <div><strong>Lap Time:</strong> {driver.currentTime?.toFixed(3)}s</div>
                        <div><strong>Sector:</strong> {driver.sector}</div>
                        <div><strong>Delta:</strong> {driver.deltaToLeader?.toFixed(3)}s</div>
                        <div><strong>Avg:</strong> {driver.avgLapTime}s</div>
                        <div><strong>Best:</strong> {driver.bestLapTime}s</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Pit Decision Panel */}
          {raceStarted && latestUpdate && (
            <PitDecisionPanel 
              raceId={raceId}
              driverId={latestUpdate.drivers?.[0]?.id}
              currentLap={currentLap}
              tireAge={tireAge}
            />
          )}

          {/* Traffic Map */}
          {latestUpdate && latestUpdate.drivers && (
            <TrafficMap 
              drivers={latestUpdate.drivers}
              currentLap={currentLap}
              sector={latestUpdate.drivers[0]?.sector}
            />
          )}

          {/* Charts */}
          {updates && updates.length > 0 && (
            <div style={{ marginBottom: 30 }}>
              <div style={{ 
                marginBottom: 20,
                padding: 20,
                backgroundColor: 'white',
                borderRadius: 8,
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
              }}>
                <LapChart data={updates} />
              </div>
              <div style={{ 
                marginBottom: 20,
                padding: 20,
                backgroundColor: 'white',
                borderRadius: 8,
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
              }}>
                <DeltaChart data={updates} />
              </div>
            </div>
          )}

          {/* Update History */}
          <div style={{ 
            border: '1px solid #ddd',
            borderRadius: 8,
            padding: 15,
            backgroundColor: 'white',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}>
            <h2 style={{ marginTop: 0, color: '#333' }}>📜 Update History ({updates?.length || 0} updates)</h2>
            <div style={{ 
              maxHeight: 200, 
              overflowY: 'auto',
              border: '1px solid #eee',
              borderRadius: 4,
              padding: 10,
              backgroundColor: '#fafafa'
            }}>
              {!updates || updates.length === 0 ? (
                <p style={{ color: '#999', textAlign: 'center' }}>No updates yet. Start the race simulation to see live updates!</p>
              ) : (
                updates.slice().reverse().map((update, idx) => (
                  <div 
                    key={idx} 
                    style={{ 
                      padding: '8px 0', 
                      borderBottom: '1px solid #eee',
                      fontSize: '13px',
                      color: '#666'
                    }}
                  >
                    <strong>{new Date(update.timestamp).toLocaleTimeString()}</strong> - 
                    Lap {update.lap} | 
                    {update.drivers?.length || 0} drivers | 
                    {update.drivers?.[0]?.sector || 'N/A'}
                  </div>
                ))
              )}
            </div>
          </div>
        </>
      )}

      {/* Strategy Tab */}
      {activeTab === 'strategy' && (
        <div>
          <StrategyConsole raceId={raceId} driverId={stats?.[0]?.id} />
          
          {/* AI Agent Panel */}
          {latestUpdate && (
            <div style={{ marginTop: 30 }}>
              <AIAgentPanel 
                raceId={raceId}
                driverId={stats?.[0]?.id || 'driver_1'}
                liveData={latestUpdate}
              />
            </div>
          )}
        </div>
      )}

      {/* Comparison Tab */}
      {activeTab === 'comparison' && (
        <div>
          {latestUpdate && latestUpdate.drivers && stats && updates && (
            <MultiDriverComparison 
              drivers={stats}
              driverTwins={latestUpdate.driverTwin || {}}
              liveData={latestUpdate}
              lapData={updates.map(u => ({
                lap: u.lap,
                drivers: u.drivers
              }))}
            />
          )}
          {(!latestUpdate || !latestUpdate.drivers) && (
            <div style={{ padding: 40, textAlign: 'center', color: '#999' }}>
              Start the race simulation to see driver comparisons
            </div>
          )}
        </div>
      )}
    </div>
  );
}
