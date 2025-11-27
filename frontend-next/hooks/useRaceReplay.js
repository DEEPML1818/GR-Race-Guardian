import { create } from 'zustand';
import { getTrackPosition } from '../utils/replayUtils';

const useRaceReplay = create((set, get) => ({
    // Playback State
    isPlaying: false,
    currentTime: 0,
    playbackSpeed: 1,
    duration: 0,

    // Data State
    raceData: null, // Parsed CSV data
    trackData: null, // SVG path and coordinates
    telemetryData: null, // GPS telemetry replay data
    trackPath: [], // GPS track path coordinates
    cars: [], // Current car positions

    // Actions
    setIsPlaying: (isPlaying) => set({ isPlaying }),
    setCurrentTime: (time) => {
        set({ currentTime: time });
        get().updateCars(time);
    },
    setPlaybackSpeed: (speed) => set({ playbackSpeed: speed }),

    setRaceData: (data) => {
        // Calculate duration from data
        // Assuming data is sorted by timestamp or has a 'timestamp' field
        let maxTime = 0;
        if (data && data.length > 0) {
            // Try to find max timestamp
            const lastRow = data[data.length - 1];
            if (lastRow.timestamp) maxTime = lastRow.timestamp;
        }
        set({ raceData: data, duration: maxTime, currentTime: 0 });
    },

    setTrackData: (data) => set({ trackData: data }),

    setTelemetryData: (data) => {
        // Set telemetry replay data with GPS positions
        if (data && data.frames) {
            const duration = data.duration_seconds || 0;
            const trackPath = data.track_path || [];
            set({
                telemetryData: data,
                trackPath: trackPath,
                duration: duration,
                currentTime: 0
            });
        }
    },

    updateCars: (time) => {
        const { raceData, trackData, telemetryData } = get();

        // If we have telemetry data with GPS, use that
        if (telemetryData && telemetryData.frames) {
            get().updateCarsFromTelemetry(time);
            return;
        }

        // Otherwise use legacy CSV data
        if (!raceData || !trackData) return;

        // Logic to interpolate car positions based on time
        // For MVP, we'll use a simplified approach:
        // 1. Get unique drivers
        // 2. Calculate progress for each driver at 'time'
        // 3. Map progress to track position

        const carsList = [];

        // If raceData is empty, return
        if (!raceData.length) return;

        // Get unique drivers
        const drivers = [...new Set(raceData.map(r => r.driver))].filter(d => d);

        drivers.forEach((driver, index) => {
            // Find rows for this driver
            // Optimization: In a real app, we'd index this.
            const driverRows = raceData.filter(r => r.driver === driver);

            if (!driverRows.length) return;

            // Find the row just before current time
            // We assume rows are sorted by timestamp
            let currentRow = driverRows[0];
            let nextRow = null;

            for (let i = 0; i < driverRows.length; i++) {
                if (driverRows[i].timestamp <= time) {
                    currentRow = driverRows[i];
                } else {
                    nextRow = driverRows[i];
                    break;
                }
            }

            // If time is before first row, use first row
            if (time < driverRows[0].timestamp) {
                currentRow = driverRows[0];
                nextRow = driverRows[0];
            }

            // Calculate lap progress (0..1)
            // If we have 'lap_progress' or similar in CSV, use it.
            // Otherwise, estimate based on time within lap.

            let progress = 0;

            // If we have nextRow, interpolate
            if (nextRow && currentRow !== nextRow) {
                const timeDiff = nextRow.timestamp - currentRow.timestamp;
                const timeSinceCurrent = time - currentRow.timestamp;
                const ratio = timeDiff > 0 ? timeSinceCurrent / timeDiff : 0;

                // Assume linear progress between rows?
                // If rows are lap start/end, this is rough.
                // If rows are telemetry points (every 0.1s), this is accurate.

                // Let's assume telemetry points for now as per prompt "Parses telemetry"
                // If we don't have progress column, we might need to rely on 'lap' and 'laptime'
                // But let's try to map to track length.

                // If we have 'distance' or 'lap_distance', use that.
                // If not, we might just use time interpolation if we assume constant speed (bad assumption but ok for MVP).

                // Let's assume we have 'lap_distance_percent' or we calculate it.
                // For now, let's use a placeholder calculation:
                // progress = (currentRow.lap_distance + (nextRow.lap_distance - currentRow.lap_distance) * ratio) / trackLength

                // Fallback: Just use time-based looping for demo if data is sparse
                // progress = (time % 90) / 90; 

                // BETTER FALLBACK: Use the 'getTrackPosition' with a simulated progress
                // If we have 'lap' and 'laptime', we can estimate.

                // Let's assume the CSV has 'lap_fraction' or we compute it.
                // For this demo, let's just use a simple time-based loop offset by driver index to show movement.
                progress = ((time + index * 5) % 90) / 90;
            } else {
                progress = ((time + index * 5) % 90) / 90;
            }

            const pos = getTrackPosition(trackData, progress);

            carsList.push({
                id: driver,
                number: currentRow.car || '?',
                driver: driver,
                x: pos.x,
                y: pos.y,
                color: getColorForDriver(index)
            });
        });

        set({ cars: carsList });
    },

    updateCarsFromTelemetry: (time) => {
        const { telemetryData } = get();
        if (!telemetryData || !telemetryData.frames) return;

        const frames = telemetryData.frames;

        // Find the frame closest to current time
        let targetFrame = frames[0];
        let minDiff = Math.abs(frames[0].time_seconds - time);

        for (const frame of frames) {
            const diff = Math.abs(frame.time_seconds - time);
            if (diff < minDiff) {
                minDiff = diff;
                targetFrame = frame;
            }
        }

        // Convert frame cars to display format
        const carsList = targetFrame.cars.map((car, index) => ({
            id: car.vehicle_number,
            number: car.vehicle_number,
            vehicle_number: car.vehicle_number,
            driver: `Car ${car.vehicle_number}`,
            lap: car.lap,
            lap_progress: car.lap_progress,
            position: car.position,
            position_rank: index + 1,
            color: getColorForDriver(index)
        }));

        set({ cars: carsList });
    },

    reset: () => set({
        isPlaying: false,
        currentTime: 0,
        raceData: null,
        cars: []
    })
}));

// Helper for colors
const colors = ['#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4'];
const getColorForDriver = (index) => colors[index % colors.length];

export default useRaceReplay;
