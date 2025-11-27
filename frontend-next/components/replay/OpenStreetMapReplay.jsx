'use client';

import { useEffect, useState, useRef } from 'react';
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import useRaceReplay from '../../hooks/useRaceReplay';
import styles from '../../styles/OpenStreetMap.module.css';

// Fix for default marker icons in Leaflet with Next.js
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// GPS coordinates for tracks
const TRACK_GPS = {
    'barber': {
        center: [33.5492, -86.3789],
        zoom: 15,
        name: 'Barber Motorsports Park'
    },
    'cota': {
        center: [30.1328, -97.6411],
        zoom: 14,
        name: 'Circuit of the Americas'
    },
    'indianapolis': {
        center: [39.7950, -86.2350],
        zoom: 15,
        name: 'Indianapolis Motor Speedway'
    },
    'road-america': {
        center: [43.8014, -87.9897],
        zoom: 14,
        name: 'Road America'
    },
    'sebring': {
        center: [27.4515, -81.3485],
        zoom: 14,
        name: 'Sebring International Raceway'
    },
    'sonoma': {
        center: [38.1614, -122.4544],
        zoom: 15,
        name: 'Sonoma Raceway'
    },
    'vir': {
        center: [36.5875, -79.2025],
        zoom: 14,
        name: 'Virginia International Raceway'
    },
    'laguna-seca': {
        center: [36.5847, -121.7539],
        zoom: 15,
        name: 'WeatherTech Raceway Laguna Seca'
    }
};

// Custom car marker icon
const createCarIcon = (number, color, position) => {
    const positionColors = {
        1: '#FFD700', // Gold
        2: '#C0C0C0', // Silver
        3: '#CD7F32'  // Bronze
    };

    const fillColor = positionColors[position] || color || '#ef4444';

    return L.divIcon({
        className: 'custom-car-marker',
        html: `
            <div class="${styles.carMarker}" style="background-color: ${fillColor};">
                <span class="${styles.carNumber}">${number}</span>
            </div>
        `,
        iconSize: [30, 30],
        iconAnchor: [15, 15]
    });
};

// Component to handle map updates
function MapUpdater({ center, zoom, followedCarPosition }) {
    const map = useMap();
    const prevCenterRef = useRef(center);

    useEffect(() => {
        // If following a car, center on it
        if (followedCarPosition) {
            map.setView([followedCarPosition.lat, followedCarPosition.lon], map.getZoom(), {
                animate: true,
                duration: 0.5
            });
        }
        // Otherwise only update if center prop changes significantly (track change)
        else if (center && (center[0] !== prevCenterRef.current[0] || center[1] !== prevCenterRef.current[1])) {
            map.setView(center, zoom);
            prevCenterRef.current = center;
        }
    }, [center, zoom, map, followedCarPosition]);

    return null;
}

export default function OpenStreetMapReplay({ trackId, trackPath, cars }) {
    const [mounted, setMounted] = useState(false);
    const [followedCarId, setFollowedCarId] = useState(null);
    const { isPlaying, currentTime } = useRaceReplay();

    // Get track GPS info
    const trackGPS = TRACK_GPS[trackId] || TRACK_GPS['barber'];

    // Only render on client side
    useEffect(() => {
        setMounted(true);
    }, []);

    if (!mounted) {
        return (
            <div className={styles.loadingContainer}>
                <div className={styles.spinner}></div>
                <p>Loading map...</p>
            </div>
        );
    }

    // Convert track path to Leaflet format
    const trackPathCoords = trackPath && trackPath.length > 0
        ? trackPath.map(point => [point.lat, point.lon])
        : null;

    // Find followed car position
    const followedCar = cars ? cars.find(c => c.vehicle_number === followedCarId) : null;
    const followedCarPosition = followedCar ? followedCar.position : null;

    return (
        <div className={styles.mapContainer}>
            <MapContainer
                center={trackGPS.center}
                zoom={trackGPS.zoom}
                className={styles.map}
                zoomControl={true}
                scrollWheelZoom={true}
            >
                <MapUpdater
                    center={trackGPS.center}
                    zoom={trackGPS.zoom}
                    followedCarPosition={followedCarPosition}
                />

                {/* OpenStreetMap Tiles - Dark Mode */}
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    className={styles.tileLayer}
                />

                {/* Track Path */}
                {trackPathCoords && trackPathCoords.length > 0 && (
                    <Polyline
                        positions={trackPathCoords}
                        pathOptions={{
                            color: '#3b82f6',
                            weight: 8,
                            opacity: 0.8,
                            lineJoin: 'round',
                            lineCap: 'round'
                        }}
                    />
                )}

                {/* Car Markers */}
                {cars && cars.map((car, index) => {
                    if (!car.position || !car.position.lat || !car.position.lon) {
                        return null;
                    }

                    const isFollowed = followedCarId === car.vehicle_number;

                    return (
                        <Marker
                            key={car.vehicle_number || index}
                            position={[car.position.lat, car.position.lon]}
                            icon={createCarIcon(
                                car.vehicle_number || '?',
                                car.color || '#ef4444',
                                car.position_rank || index + 1
                            )}
                            eventHandlers={{
                                click: () => setFollowedCarId(isFollowed ? null : car.vehicle_number)
                            }}
                            zIndexOffset={isFollowed ? 1000 : 0}
                        >
                            <Popup>
                                <div className={styles.carPopup}>
                                    <strong>Car #{car.vehicle_number}</strong>
                                    <div>Lap: {car.lap || 1}</div>
                                    <div>Position: P{car.position_rank || index + 1}</div>
                                    {car.driver && <div>Driver: {car.driver}</div>}
                                    <button
                                        className={styles.followButton}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            setFollowedCarId(isFollowed ? null : car.vehicle_number);
                                        }}
                                    >
                                        {isFollowed ? 'Stop Following' : 'Follow Camera'}
                                    </button>
                                </div>
                            </Popup>
                        </Marker>
                    );
                })}
            </MapContainer>

            {/* Track Info Overlay */}
            <div className={styles.trackInfo}>
                <h3>{trackGPS.name}</h3>
                <div className={styles.trackStats}>
                    <span>{cars ? cars.length : 0} Cars</span>
                    {isPlaying && <span className={styles.liveIndicator}>● LIVE</span>}
                </div>

                {/* Camera Controls */}
                <div className="mt-2 pt-2 border-t border-gray-700">
                    <label className="text-xs text-gray-400 block mb-1">Camera Follow:</label>
                    <select
                        className="bg-gray-800 text-white text-xs p-1 rounded border border-gray-600 w-full"
                        value={followedCarId || ''}
                        onChange={(e) => setFollowedCarId(e.target.value ? parseInt(e.target.value) : null)}
                    >
                        <option value="">Free Camera</option>
                        {cars && cars.map(car => (
                            <option key={car.vehicle_number} value={car.vehicle_number}>
                                #{car.vehicle_number} {car.driver ? `- ${car.driver}` : ''}
                            </option>
                        ))}
                    </select>
                </div>
            </div>
        </div>
    );
}
