'use client';

import { useEffect, useState, useRef } from 'react';
import dynamic from 'next/dynamic';
import useRaceReplay from '../../hooks/useRaceReplay';
import { motion } from 'framer-motion';

// Dynamically import OpenStreetMap component (client-side only)
const OpenStreetMapReplay = dynamic(
    () => import('./OpenStreetMapReplay'),
    { ssr: false }
);

export default function TrackMap({ trackId }) {
    const { trackData, setTrackData, telemetryData, setTelemetryData, trackPath, cars } = useRaceReplay();
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [useOpenStreetMap, setUseOpenStreetMap] = useState(false);
    const svgRef = useRef(null);

    useEffect(() => {
        async function fetchData() {
            if (!trackId) return;

            try {
                setLoading(true);

                // 1. Fetch Track Coordinates (SVG/Info)
                const trackResponse = await fetch(`http://127.0.0.1:8000/tracks/${trackId}/coordinates`);
                if (!trackResponse.ok) {
                    throw new Error(`Failed to load track data: ${trackResponse.statusText}`);
                }
                const trackData = await trackResponse.json();
                setTrackData(trackData);

                // 2. Fetch Default Telemetry (GPS Replay)
                // This satisfies "it must do it self" - auto-loading race data
                try {
                    const replayResponse = await fetch(`http://127.0.0.1:8000/replay/telemetry/${trackId}`);
                    if (replayResponse.ok) {
                        const replayData = await replayResponse.json();
                        // Check if we got valid replay data with frames
                        if (replayData.frames && replayData.frames.length > 0) {
                            console.log("Loaded GPS telemetry data", replayData);
                            setTelemetryData(replayData);
                        } else {
                            console.log("No GPS data available, using SVG fallback");
                        }
                    }
                } catch (e) {
                    console.warn("Could not load default telemetry:", e);
                    // Don't fail the whole component, just fallback to no telemetry
                }

                setLoading(false);
            } catch (err) {
                console.error("Error fetching data:", err);
                setError(err.message);
                setLoading(false);
            }
        }

        fetchData();
    }, [trackId, setTrackData, setTelemetryData]);

    // Determine if we should use OpenStreetMap
    useEffect(() => {
        // Use OpenStreetMap if we have telemetry data with GPS positions
        if (telemetryData && trackPath && trackPath.length > 0) {
            setUseOpenStreetMap(true);
        } else {
            setUseOpenStreetMap(false);
        }
    }, [telemetryData, trackPath]);

    if (loading) {
        return (
            <div className="w-full h-full flex items-center justify-center text-gray-400">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mr-3"></div>
                Loading Track Map...
            </div>
        );
    }

    if (error) {
        return (
            <div className="w-full h-full flex items-center justify-center text-red-400">
                Error: {error}
            </div>
        );
    }

    // Use OpenStreetMap if telemetry data is available
    if (useOpenStreetMap) {
        return (
            <OpenStreetMapReplay
                trackId={trackId}
                trackPath={trackPath}
                cars={cars}
            />
        );
    }

    // Fallback to SVG rendering
    if (!trackData || !trackData.svg_path) {
        return (
            <div className="w-full h-full flex items-center justify-center text-gray-500">
                No map data available for {trackId}
            </div>
        );
    }

    return (
        <div className="w-full h-full p-4 flex items-center justify-center bg-black">
            <div className="relative w-full h-full max-w-4xl max-h-[80vh] aspect-square">
                <svg
                    ref={svgRef}
                    viewBox="0 0 1000 1000"
                    className="w-full h-full drop-shadow-[0_0_15px_rgba(59,130,246,0.5)]"
                    preserveAspectRatio="xMidYMid meet"
                >
                    {/* Track Path */}
                    <path
                        d={trackData.svg_path}
                        fill="none"
                        stroke="#1e293b"
                        strokeWidth="20"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    />
                    <path
                        d={trackData.svg_path}
                        fill="none"
                        stroke="#3b82f6"
                        strokeWidth="6"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        className="opacity-80"
                    />

                    {/* Cars */}
                    {cars.map((car, index) => (
                        <motion.g
                            key={car.id || index}
                            initial={{ x: car.x, y: car.y }}
                            animate={{ x: car.x, y: car.y }}
                            transition={{ type: "tween", ease: "linear", duration: 0.1 }}
                        >
                            <circle r="8" fill={car.color || "#ef4444"} stroke="white" strokeWidth="2" />
                            <text
                                y="-12"
                                textAnchor="middle"
                                fill="white"
                                fontSize="12"
                                fontWeight="bold"
                                className="pointer-events-none select-none drop-shadow-md"
                            >
                                {car.number}
                            </text>
                        </motion.g>
                    ))}
                </svg>
            </div>
        </div>
    );
}
