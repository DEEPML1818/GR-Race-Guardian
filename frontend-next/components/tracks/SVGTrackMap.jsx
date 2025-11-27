/**
 * SVG Track Map Component
 * 
 * Renders interactive SVG track layout with driver positions
 */

import { useEffect, useState } from 'react';
import styles from '../../styles/TrackReplay.module.css';

export default function SVGTrackMap({ trackId, currentLap, driverPositions }) {
    const [trackData, setTrackData] = useState(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (trackId) {
            fetchTrackData();
        }
    }, [trackId]);

    const fetchTrackData = async () => {
        setLoading(true);
        try {
            const response = await fetch(`http://127.0.0.1:8000/tracks/${trackId}/coordinates`);
            const data = await response.json();
            if (data.success) {
                setTrackData(data);
            }
        } catch (err) {
            console.error('Failed to fetch track data:', err);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className={styles.trackMapLoading}>
                <div className={styles.spinner}></div>
                <p>Loading track map...</p>
            </div>
        );
    }

    if (!trackData || !trackData.svg_path) {
        return (
            <div className={styles.trackMapPlaceholder}>
                <p>Track map not available</p>
                <p className={styles.trackMapHint}>Track: {trackId}</p>
            </div>
        );
    }

    // Calculate driver positions on track
    const getDriverTrackPosition = (driver) => {
        if (!trackData.coordinates || trackData.coordinates.length === 0) {
            return null;
        }

        // Simple approximation: distribute drivers along the track based on their lap completion
        const totalPoints = trackData.coordinates.length;
        const lapProgress = driver.laps_completed / currentLap;
        const pointIndex = Math.floor(lapProgress * totalPoints) % totalPoints;

        const point = trackData.coordinates[pointIndex];
        return {
            x: point.x * 1000, // Scale to viewBox
            y: point.y * 1000,
            driver: driver.driver,
            position: driver.position
        };
    };

    const driverMarkers = driverPositions
        ?.map(getDriverTrackPosition)
        .filter(pos => pos !== null) || [];

    return (
        <div className={styles.svgTrackMapContainer}>
            <svg
                viewBox="0 0 1000 1000"
                className={styles.trackSvg}
                xmlns="http://www.w3.org/2000/svg"
            >
                {/* Track outline */}
                <path
                    d={trackData.svg_path}
                    fill="none"
                    stroke="#333"
                    strokeWidth="40"
                    className={styles.trackOutline}
                />

                {/* Track surface */}
                <path
                    d={trackData.svg_path}
                    fill="none"
                    stroke="#1a1f3a"
                    strokeWidth="30"
                    className={styles.trackSurface}
                />

                {/* Track center line */}
                <path
                    d={trackData.svg_path}
                    fill="none"
                    stroke="rgba(255, 255, 255, 0.1)"
                    strokeWidth="2"
                    strokeDasharray="10,10"
                    className={styles.trackCenterLine}
                />

                {/* Start/Finish line */}
                {trackData.coordinates && trackData.coordinates[0] && (
                    <g>
                        <rect
                            x={trackData.coordinates[0].x * 1000 - 20}
                            y={trackData.coordinates[0].y * 1000 - 5}
                            width="40"
                            height="10"
                            fill="white"
                            opacity="0.8"
                        />
                        <text
                            x={trackData.coordinates[0].x * 1000}
                            y={trackData.coordinates[0].y * 1000 - 15}
                            textAnchor="middle"
                            fill="white"
                            fontSize="12"
                            fontWeight="bold"
                        >
                            START/FINISH
                        </text>
                    </g>
                )}

                {/* Driver markers */}
                {driverMarkers.map((marker, idx) => (
                    <g key={idx} className={styles.driverMarker}>
                        {/* Car circle */}
                        <circle
                            cx={marker.x}
                            cy={marker.y}
                            r="8"
                            fill={marker.position === 1 ? '#FFD700' : marker.position === 2 ? '#C0C0C0' : marker.position === 3 ? '#CD7F32' : '#ff4444'}
                            stroke="white"
                            strokeWidth="2"
                            className={styles.carMarker}
                        >
                            <animate
                                attributeName="r"
                                values="8;10;8"
                                dur="2s"
                                repeatCount="indefinite"
                            />
                        </circle>

                        {/* Position number */}
                        <text
                            x={marker.x}
                            y={marker.y + 4}
                            textAnchor="middle"
                            fill="white"
                            fontSize="10"
                            fontWeight="bold"
                            pointerEvents="none"
                        >
                            {marker.position}
                        </text>

                        {/* Driver label */}
                        <text
                            x={marker.x}
                            y={marker.y - 15}
                            textAnchor="middle"
                            fill="white"
                            fontSize="10"
                            className={styles.driverLabel}
                        >
                            {marker.driver}
                        </text>
                    </g>
                ))}
            </svg>

            {/* Track info overlay */}
            <div className={styles.trackInfoOverlay}>
                <div className={styles.trackName}>{trackData.track_info?.name || trackId}</div>
                <div className={styles.trackStats}>
                    {trackData.track_info?.length && (
                        <span>{trackData.track_info.length} mi</span>
                    )}
                    {trackData.track_info?.turns && (
                        <span>{trackData.track_info.turns} turns</span>
                    )}
                </div>
            </div>
        </div>
    );
}
