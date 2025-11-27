import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import TrackMapView from '../components/tracks/TrackMapView';
import RaceReplay from '../components/tracks/RaceReplay';
import dynamic from 'next/dynamic';

const TrackLive = dynamic(() => import('../components/tracks/TrackLive'), { ssr: false });

export default function TracksPage() {
  const router = useRouter();
  const [tracks, setTracks] = useState([]);
  const [selectedTrack, setSelectedTrack] = useState(null);
  const [selectedRace, setSelectedRace] = useState(null);
  const [raceData, setRaceData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [raceTime, setRaceTime] = useState(0);
  const [mode, setMode] = useState('replay');

  useEffect(() => {
    fetchAvailableTracks();
  }, []);

  useEffect(() => {
    if (selectedTrack && selectedRace) {
      fetchRaceData();
    }
  }, [selectedTrack, selectedRace]);

  const fetchAvailableTracks = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/tracks/available');
      const data = await response.json();
      console.log('Tracks API Response:', data);

      if (data.success && data.tracks && data.tracks.length > 0) {
        setTracks(data.tracks);
        setSelectedTrack(data.tracks[0].id);
        if (data.tracks[0].races && data.tracks[0].races.length > 0) {
          setSelectedRace(data.tracks[0].races[0].id);
        } else {
          // Set default race if none found
          setSelectedRace('race-1');
        }
      } else {
        console.warn('No tracks returned from API, using fallback');
        // Fallback tracks if API fails
        const fallbackTracks = [
          { id: "barber", name: "Barber Motorsports Park", races: [{ id: "race-1", name: "Race 1" }] },
          { id: "cota", name: "Circuit of the Americas", races: [{ id: "race-1", name: "Race 1" }] },
          { id: "indianapolis", name: "Indianapolis Motor Speedway", races: [{ id: "race-1", name: "Race 1" }] },
          { id: "road-america", name: "Road America", races: [{ id: "race-1", name: "Race 1" }] },
          { id: "sebring", name: "Sebring International Raceway", races: [{ id: "race-1", name: "Race 1" }] },
          { id: "sonoma", name: "Sonoma Raceway", races: [{ id: "race-1", name: "Race 1" }] },
          { id: "vir", name: "Virginia International Raceway", races: [{ id: "race-1", name: "Race 1" }] }
        ];
        setTracks(fallbackTracks);
        setSelectedTrack(fallbackTracks[0].id);
        setSelectedRace('race-1');
      }
    } catch (error) {
      console.error('Failed to fetch tracks:', error);
      // Fallback tracks on error
      const fallbackTracks = [
        { id: "barber", name: "Barber Motorsports Park", races: [{ id: "race-1", name: "Race 1" }] },
        { id: "cota", name: "Circuit of the Americas", races: [{ id: "race-1", name: "Race 1" }] },
        { id: "indianapolis", name: "Indianapolis Motor Speedway", races: [{ id: "race-1", name: "Race 1" }] },
        { id: "road-america", name: "Road America", races: [{ id: "race-1", name: "Race 1" }] },
        { id: "sebring", name: "Sebring International Raceway", races: [{ id: "race-1", name: "Race 1" }] },
        { id: "sonoma", name: "Sonoma Raceway", races: [{ id: "race-1", name: "Race 1" }] },
        { id: "vir", name: "Virginia International Raceway", races: [{ id: "race-1", name: "Race 1" }] }
      ];
      setTracks(fallbackTracks);
      setSelectedTrack(fallbackTracks[0].id);
      setSelectedRace('race-1');
    } finally {
      setLoading(false);
    }
  };

  const fetchRaceData = async () => {
    if (!selectedTrack || !selectedRace) return;

    setLoading(true);
    try {
      // Always fetch coordinates first (they should always work)
      const coordsResponse = await fetch(`http://127.0.0.1:8000/tracks/${selectedTrack}/coordinates`);
      const coordsData = await coordsResponse.json();

      // Try to fetch replay data
      let replayData = { success: false, results: [], lap_progression: [] };
      try {
        const replayResponse = await fetch('http://127.0.0.1:8000/tracks/replay', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            track_id: selectedTrack,
            race_id: selectedRace
          })
        });
        replayData = await replayResponse.json();
      } catch (replayError) {
        console.warn('Replay data failed, using coordinates only:', replayError);
      }

      console.log('Replay Data:', replayData);
      console.log('Coordinates Data:', coordsData);

      // Always set data if coordinates are available
      if (coordsData.success) {
        setRaceData({
          replay: replayData.success ? replayData : { results: [], lap_progression: [] },
          coordinates: coordsData
        });
      } else {
        console.error('Failed to load coordinates:', coordsData);
        // Even if coordinates fail, show something
        setRaceData({
          replay: replayData.success ? replayData : { results: [], lap_progression: [] },
          coordinates: {
            track_info: { name: currentTrack?.name || 'Unknown Track', length: 0, turns: 0 },
            coordinates: [],
            svg_path: ''
          }
        });
      }
    } catch (error) {
      console.error('Failed to fetch race data:', error);
      // Set minimal data so UI doesn't break
      setRaceData({
        replay: { results: [], lap_progression: [] },
        coordinates: {
          track_info: { name: currentTrack?.name || 'Unknown Track', length: 0, turns: 0 },
          coordinates: [],
          svg_path: ''
        }
      });
    } finally {
      setLoading(false);
    }
  };

  const currentTrack = tracks.find(t => t.id === selectedTrack);

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#f5f5f5',
      padding: '20px'
    }}>
      <div style={{
        maxWidth: '1400px',
        margin: '0 auto',
        backgroundColor: 'white',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        padding: '30px'
      }}>
        <h1 style={{
          fontSize: '32px',
          fontWeight: 'bold',
          marginBottom: '10px',
          color: '#333'
        }}>
          🏁 Race Track Visualization
        </h1>
        <p style={{ color: '#666', marginBottom: '30px' }}>
          View race progression and track layouts for all available tracks
        </p>

        {/* Track Selection */}
        <div style={{
          marginBottom: '30px',
          padding: '20px',
          backgroundColor: '#f9f9f9',
          borderRadius: '6px'
        }}>
          <h2 style={{ fontSize: '18px', marginBottom: '15px', color: '#333' }}>
            Select Track & Race
          </h2>

          <div style={{ display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: '200px' }}>
              <label style={{ display: 'block', marginBottom: '5px', color: '#666' }}>
                Track:
              </label>
              <select
                value={selectedTrack || ''}
                onChange={(e) => {
                  setSelectedTrack(e.target.value);
                  const track = tracks.find(t => t.id === e.target.value);
                  if (track && track.races && track.races.length > 0) {
                    setSelectedRace(track.races[0].id);
                  }
                }}
                style={{
                  width: '100%',
                  padding: '10px',
                  borderRadius: '4px',
                  border: '1px solid #ddd',
                  fontSize: '14px'
                }}
              >
                {tracks.map(track => (
                  <option key={track.id} value={track.id}>
                    {track.name}
                  </option>
                ))}
              </select>
            </div>

            {currentTrack && currentTrack.races && (
              <div style={{ flex: 1, minWidth: '200px' }}>
                <label style={{ display: 'block', marginBottom: '5px', color: '#666' }}>
                  Race:
                </label>
                <select
                  value={selectedRace || ''}
                  onChange={(e) => setSelectedRace(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px',
                    borderRadius: '4px',
                    border: '1px solid #ddd',
                    fontSize: '14px'
                  }}
                >
                  {currentTrack.races.map(race => (
                    <option key={race.id} value={race.id}>
                      {race.name}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <div style={{ fontSize: '18px', color: '#666' }}>Loading race data...</div>
          </div>
        )}

        {/* Track Map / Live Toggle and Replay */}
        {!loading && raceData && (
          <div>
            <div style={{ marginBottom: 12, display: 'flex', gap: 8 }}>
              <button onClick={() => setMode('replay')} style={{ padding: '8px 12px', borderRadius: 6, background: mode === 'replay' ? '#1976d2' : '#eee', color: mode === 'replay' ? '#fff' : '#333', border: 'none' }}>Replay</button>
              <button onClick={() => setMode('live')} style={{ padding: '8px 12px', borderRadius: 6, background: mode === 'live' ? '#1976d2' : '#eee', color: mode === 'live' ? '#fff' : '#333', border: 'none' }}>Live</button>
            </div>

            {mode === 'replay' ? (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                <div>
                  <TrackMapView
                    trackId={selectedTrack}
                    trackInfo={raceData.coordinates?.track_info || {
                      name: currentTrack?.name || 'Unknown Track',
                      length: 0,
                      turns: 0
                    }}
                    coordinates={raceData.coordinates?.coordinates || []}
                    svgPath={raceData.coordinates?.svg_path || ''}
                    raceResults={raceData.replay?.results || []}
                    raceTime={raceTime}
                    lapProgression={raceData.replay?.lap_progression || []}
                  />
                </div>
                <div>
                  <RaceReplay
                    replayData={raceData.replay || { results: [], lap_progression: [] }}
                    trackId={selectedTrack}
                    onTimeChange={setRaceTime}
                  />
                </div>
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '20px' }}>
                <div>
                  <TrackLive trackId={selectedTrack} raceId={selectedRace} />
                </div>
                <div>
                  <RaceReplay
                    replayData={raceData.replay || { results: [], lap_progression: [] }}
                    trackId={selectedTrack}
                    onTimeChange={setRaceTime}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Show track even if no race data */}
        {!loading && !raceData && selectedTrack && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div>
              <TrackMapView
                trackId={selectedTrack}
                trackInfo={{
                  name: currentTrack?.name || 'Unknown Track',
                  length: 0,
                  turns: 0
                }}
                coordinates={[]}
                svgPath=""
                raceResults={[]}
              />
            </div>
            <div style={{
              backgroundColor: 'white',
              borderRadius: '8px',
              padding: '20px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
            }}>
              <h2 style={{ fontSize: '20px', marginBottom: '15px', color: '#333' }}>
                Race Replay
              </h2>
              <p style={{ color: '#666' }}>
                Select a race to view replay data.
              </p>
            </div>
          </div>
        )}

        {/* Debug Info */}
        {!loading && raceData && process.env.NODE_ENV === 'development' && (
          <div style={{
            marginTop: '20px',
            padding: '15px',
            backgroundColor: '#f0f0f0',
            borderRadius: '6px',
            fontSize: '12px',
            fontFamily: 'monospace'
          }}>
            <strong>Debug Info:</strong>
            <pre style={{ marginTop: '10px', overflow: 'auto', maxHeight: '200px' }}>
              {JSON.stringify({
                hasTrackInfo: !!raceData.coordinates?.track_info,
                hasCoordinates: !!raceData.coordinates?.coordinates,
                coordinatesCount: raceData.coordinates?.coordinates?.length || 0,
                hasSvgPath: !!raceData.coordinates?.svg_path,
                svgPathLength: raceData.coordinates?.svg_path?.length || 0,
                hasResults: !!raceData.replay?.results,
                resultsCount: raceData.replay?.results?.length || 0
              }, null, 2)}
            </pre>
          </div>
        )}

        {/* No Data Message */}
        {!loading && !raceData && (
          <div style={{
            textAlign: 'center',
            padding: '40px',
            color: '#999'
          }}>
            <p style={{ marginBottom: '10px' }}>No race data available. Please select a track and race.</p>
            <p style={{ fontSize: '14px', color: '#666' }}>
              {selectedTrack && selectedRace ?
                'Loading data...' :
                'Make sure both track and race are selected.'}
            </p>
            {selectedTrack && (
              <div style={{
                marginTop: '20px',
                padding: '15px',
                backgroundColor: '#f0f0f0',
                borderRadius: '6px',
                fontSize: '12px',
                textAlign: 'left',
                maxWidth: '600px',
                margin: '20px auto'
              }}>
                <strong>Debug Info:</strong>
                <div>Selected Track: {selectedTrack}</div>
                <div>Selected Race: {selectedRace || 'None'}</div>
                <div>Available Tracks: {tracks.length}</div>
                {currentTrack && (
                  <div>Current Track Races: {currentTrack.races?.length || 0}</div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

