'use client';

import { useState, useEffect, useMemo } from 'react';

export default function TrackMapView({ trackId, trackInfo, coordinates, svgPath, raceResults, raceTime, lapProgression }) {
  const [selectedDriver, setSelectedDriver] = useState(null);
  const [driverPositions, setDriverPositions] = useState([]);

  // Pre-process lap data by driver for faster lookup
  const driverLapTimes = useMemo(() => {
    if (!lapProgression) return {};

    const times = {};
    lapProgression.forEach(lapData => {
      if (lapData.positions) {
        lapData.positions.forEach(pos => {
          if (!times[pos.vehicle_number]) {
            times[pos.vehicle_number] = [];
          }
          times[pos.vehicle_number].push({
            lap: lapData.lap,
            cumulative_time: pos.cumulative_time,
            position: pos.position
          });
        });
      }
    });

    // Sort by lap for each driver
    Object.keys(times).forEach(driver => {
      times[driver].sort((a, b) => a.lap - b.lap);
    });

    return times;
  }, [lapProgression]);

  // Calculate driver positions on track based on raceTime
  useEffect(() => {
    if (!coordinates || coordinates.length === 0 || !raceTime) {
      setDriverPositions([]);
      return;
    }

    const positions = [];
    const trackLength = coordinates.length;

    Object.keys(driverLapTimes).forEach(vehicleNumber => {
      const laps = driverLapTimes[vehicleNumber];

      // Find current lap segment
      // We need to find the lap where startTime <= raceTime < endTime
      let currentLapData = null;
      let prevLapData = null;

      for (let i = 0; i < laps.length; i++) {
        if (laps[i].cumulative_time >= raceTime) {
          currentLapData = laps[i];
          prevLapData = i > 0 ? laps[i - 1] : null;
          break;
        }
      }

      // If raceTime is past the last lap, use the last lap
      if (!currentLapData && laps.length > 0 && raceTime > laps[laps.length - 1].cumulative_time) {
        // Car has finished, stay at finish line or handle as finished
        // For now, let's just show them at finish line of last lap
        currentLapData = laps[laps.length - 1];
        prevLapData = laps.length > 1 ? laps[laps.length - 2] : null;
      }

      if (currentLapData) {
        const startTime = prevLapData ? prevLapData.cumulative_time : 0;
        const endTime = currentLapData.cumulative_time;
        const lapDuration = endTime - startTime;

        // Calculate progress within the lap (0 to 1)
        let progress = 0;
        if (raceTime >= endTime) {
          progress = 1; // Finished lap
        } else if (raceTime <= startTime) {
          progress = 0; // Not started lap
        } else {
          progress = (raceTime - startTime) / lapDuration;
        }

        // Map progress to track coordinate
        // progress 0 = start/finish, 1 = start/finish (next lap)
        const trackIndex = Math.floor(progress * (trackLength - 1));
        const coord = coordinates[trackIndex] || coordinates[0];

        positions.push({
          vehicle_number: vehicleNumber,
          position: currentLapData.position, // Use position from end of this lap (approximate)
          x: coord.x * 1000,
          y: coord.y * 1000,
          progress: progress,
          lap: currentLapData.lap
        });
      }
    });

    setDriverPositions(positions);
  }, [raceTime, coordinates, driverLapTimes]);

  // Fallback track visualization if no SVG path
  const renderFallbackTrack = () => {
    // Create a simple oval track
    const centerX = 500;
    const centerY = 500;
    const radiusX = 400;
    const radiusY = 300;

    // Create path for oval using arc commands
    const path = `M ${centerX - radiusX} ${centerY} A ${radiusX} ${radiusY} 0 1 1 ${centerX + radiusX} ${centerY} A ${radiusX} ${radiusY} 0 1 1 ${centerX - radiusX} ${centerY} Z`;

    return (
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 1000 1000"
        preserveAspectRatio="xMidYMid meet"
      >
        {/* Track Background */}
        <path
          d={path}
          fill="#2a2a2a"
          stroke="#444"
          strokeWidth="60"
          opacity="0.3"
        />
        {/* Track Outline */}
        <path
          d={path}
          fill="none"
          stroke="#666"
          strokeWidth="30"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {/* Track Inner Edge */}
        <path
          d={path}
          fill="none"
          stroke="#888"
          strokeWidth="25"
        />
        {/* Center Line */}
        <path
          d={path}
          fill="none"
          stroke="#fff"
          strokeWidth="3"
          strokeDasharray="15,10"
          opacity="0.6"
        />
        {/* Start/Finish Line */}
        <line
          x1={centerX - radiusX}
          y1={centerY}
          x2={centerX - radiusX + 100}
          y2={centerY}
          stroke="#ff0000"
          strokeWidth="6"
          strokeLinecap="round"
        />
        <text
          x={centerX - radiusX + 50}
          y={centerY - 20}
          textAnchor="middle"
          fill="#ff0000"
          fontSize="20"
          fontWeight="bold"
          stroke="#fff"
          strokeWidth="0.5"
        >
          S/F
        </text>
      </svg>
    );
  };

  if (!trackInfo || !coordinates) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#999' }}>
        <div style={{ marginBottom: '20px' }}>Track data not available</div>
        <div style={{
          width: '100%',
          height: '400px',
          border: '2px solid #ddd',
          borderRadius: '6px',
          backgroundColor: '#1a1a1a'
        }}>
          {renderFallbackTrack()}
        </div>
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
        {trackInfo.name}
      </h2>

      <div style={{ marginBottom: '10px', color: '#666', fontSize: '14px' }}>
        <span>Length: {trackInfo.length} miles</span>
        <span style={{ marginLeft: '15px' }}>Turns: {trackInfo.turns}</span>
      </div>

      {/* Track SVG Visualization */}
      <div style={{
        width: '100%',
        height: '500px',
        border: '2px solid #ddd',
        borderRadius: '6px',
        backgroundColor: '#1a1a1a',
        position: 'relative',
        overflow: 'visible',
        marginBottom: '20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        {svgPath ? (
          <svg
            width="100%"
            height="100%"
            viewBox="0 0 1000 1000"
            preserveAspectRatio="xMidYMid meet"
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%'
            }}
          >
            {/* Track Background (wider path for track surface) */}
            <path
              d={svgPath}
              fill="#2a2a2a"
              stroke="#444"
              strokeWidth="60"
              strokeLinecap="round"
              strokeLinejoin="round"
              opacity="0.3"
            />

            {/* Track Path (main track outline) */}
            <path
              d={svgPath}
              fill="none"
              stroke="#666"
              strokeWidth="30"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {/* Track Inner Edge */}
            <path
              d={svgPath}
              fill="none"
              stroke="#888"
              strokeWidth="25"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {/* Track Center Line */}
            <path
              d={svgPath}
              fill="none"
              stroke="#fff"
              strokeWidth="3"
              strokeDasharray="15,10"
              opacity="0.6"
            />

            {/* Start/Finish Line */}
            {coordinates && coordinates.find(c => c.type === 'start_finish') && (() => {
              const sf = coordinates.find(c => c.type === 'start_finish');
              return (
                <g>
                  <line
                    x1={sf.x * 1000 - 50}
                    y1={sf.y * 1000}
                    x2={sf.x * 1000 + 50}
                    y2={sf.y * 1000}
                    stroke="#ff0000"
                    strokeWidth="6"
                    strokeLinecap="round"
                  />
                  <text
                    x={sf.x * 1000}
                    y={sf.y * 1000 - 30}
                    textAnchor="middle"
                    fill="#ff0000"
                    fontSize="20"
                    fontWeight="bold"
                    stroke="#fff"
                    strokeWidth="0.5"
                  >
                    S/F
                  </text>
                </g>
              );
            })()}

            {/* Real Driver Positions from Race Data */}
            {driverPositions && driverPositions.length > 0 ? (
              driverPositions.map((driver, idx) => {
                // Determine color based on position (approximate)
                // We can use the position from the current lap data
                const isPodium = driver.position <= 3;
                const fillColor = driver.position === 1 ? '#FFD700' :
                  driver.position === 2 ? '#C0C0C0' :
                    driver.position === 3 ? '#CD7F32' : '#4CAF50';

                return (
                  <g key={`${driver.vehicle_number}`}>
                    {/* Driver car marker */}
                    <circle
                      cx={driver.x}
                      cy={driver.y}
                      r="20"
                      fill={fillColor}
                      stroke="#fff"
                      strokeWidth="3"
                      style={{
                        cursor: 'pointer',
                        transition: 'cx 0.1s linear, cy 0.1s linear' // Smooth transition
                      }}
                      onClick={() => {
                        const result = raceResults?.find(r => r.vehicle_number === driver.vehicle_number);
                        if (result) setSelectedDriver(result);
                      }}
                      opacity="0.95"
                    />
                    {/* Position number inside circle */}
                    <text
                      x={driver.x}
                      y={driver.y + 6}
                      textAnchor="middle"
                      fill="#fff"
                      fontSize="12"
                      fontWeight="bold"
                      stroke="#000"
                      strokeWidth="0.5"
                      style={{ transition: 'x 0.1s linear, y 0.1s linear' }}
                    >
                      {driver.position}
                    </text>
                    {/* Vehicle number above */}
                    <text
                      x={driver.x}
                      y={driver.y - 30}
                      textAnchor="middle"
                      fill="#fff"
                      fontSize="13"
                      fontWeight="bold"
                      stroke="#000"
                      strokeWidth="1"
                      style={{ transition: 'x 0.1s linear, y 0.1s linear' }}
                    >
                      #{driver.vehicle_number}
                    </text>
                  </g>
                );
              })
            ) : raceResults && raceResults.length > 0 ? (
              // Fallback: show results if no real positions available
              raceResults.slice(0, 20).map((result, idx) => {
                const angle = (idx / raceResults.length) * 2 * Math.PI - Math.PI / 2;
                const radius = 350;
                const centerX = 500;
                const centerY = 500;
                const x = centerX + radius * Math.cos(angle);
                const y = centerY + radius * Math.sin(angle);

                return (
                  <g key={`${result.vehicle_number}-${idx}`}>
                    <circle
                      cx={x}
                      cy={y}
                      r="18"
                      fill={idx === 0 ? '#FFD700' : idx === 1 ? '#C0C0C0' : idx === 2 ? '#CD7F32' : '#4CAF50'}
                      stroke="#fff"
                      strokeWidth="3"
                      style={{ cursor: 'pointer' }}
                      onClick={() => setSelectedDriver(result)}
                      opacity="0.9"
                    />
                    <text
                      x={x}
                      y={y - 30}
                      textAnchor="middle"
                      fill="#fff"
                      fontSize="14"
                      fontWeight="bold"
                      stroke="#000"
                      strokeWidth="0.5"
                    >
                      #{result.vehicle_number}
                    </text>
                    <text
                      x={x}
                      y={y + 35}
                      textAnchor="middle"
                      fill="#fff"
                      fontSize="11"
                      stroke="#000"
                      strokeWidth="0.5"
                    >
                      P{result.position}
                    </text>
                  </g>
                );
              })
            ) : null}
          </svg>
        ) : (
          <div style={{ position: 'relative', width: '100%', height: '100%' }}>
            {renderFallbackTrack()}
            <div style={{
              textAlign: 'center',
              padding: '15px',
              position: 'absolute',
              bottom: '20px',
              left: '50%',
              transform: 'translateX(-50%)',
              backgroundColor: 'rgba(0,0,0,0.8)',
              borderRadius: '6px',
              color: '#fff',
              fontSize: '12px'
            }}>
              <div style={{ marginBottom: '5px', fontWeight: 'bold' }}>
                Track layout loading...
              </div>
              <div style={{ opacity: 0.8 }}>
                Using fallback visualization
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Race Results Table */}
      {raceResults && (
        <div>
          <h3 style={{ fontSize: '16px', marginBottom: '10px', color: '#333' }}>
            Race Results
          </h3>
          <div style={{
            maxHeight: '300px',
            overflowY: 'auto',
            border: '1px solid #ddd',
            borderRadius: '4px'
          }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead style={{ backgroundColor: '#f5f5f5', position: 'sticky', top: 0 }}>
                <tr>
                  <th style={{ padding: '10px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Pos</th>
                  <th style={{ padding: '10px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>#</th>
                  <th style={{ padding: '10px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Laps</th>
                  <th style={{ padding: '10px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Time</th>
                  <th style={{ padding: '10px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Gap</th>
                </tr>
              </thead>
              <tbody>
                {raceResults.map((result, idx) => (
                  <tr
                    key={result.vehicle_number}
                    style={{
                      backgroundColor: selectedDriver?.vehicle_number === result.vehicle_number ? '#e3f2fd' : 'white',
                      cursor: 'pointer'
                    }}
                    onClick={() => setSelectedDriver(result)}
                  >
                    <td style={{ padding: '10px', borderBottom: '1px solid #eee' }}>
                      <span style={{
                        display: 'inline-block',
                        width: '24px',
                        height: '24px',
                        borderRadius: '50%',
                        backgroundColor: idx === 0 ? '#FFD700' : idx === 1 ? '#C0C0C0' : idx === 2 ? '#CD7F32' : '#e0e0e0',
                        textAlign: 'center',
                        lineHeight: '24px',
                        fontSize: '12px',
                        fontWeight: 'bold',
                        color: idx < 3 ? '#fff' : '#333'
                      }}>
                        {result.position}
                      </span>
                    </td>
                    <td style={{ padding: '10px', borderBottom: '1px solid #eee', fontWeight: 'bold' }}>
                      #{result.vehicle_number}
                    </td>
                    <td style={{ padding: '10px', borderBottom: '1px solid #eee' }}>
                      {result.laps}
                    </td>
                    <td style={{ padding: '10px', borderBottom: '1px solid #eee' }}>
                      {result.total_time}
                    </td>
                    <td style={{ padding: '10px', borderBottom: '1px solid #eee', color: '#666' }}>
                      {result.gap_first}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

