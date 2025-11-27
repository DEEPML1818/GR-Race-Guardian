'use client';

import { useEffect, useRef } from 'react';
import useRaceReplay from '../../hooks/useRaceReplay';

export default function ReplayController() {
    const {
        isPlaying, setIsPlaying,
        currentTime, setCurrentTime,
        duration,
        playbackSpeed, setPlaybackSpeed
    } = useRaceReplay();

    const requestRef = useRef();
    const previousTimeRef = useRef();

    const animate = (time) => {
        if (previousTimeRef.current !== undefined) {
            const deltaTime = time - previousTimeRef.current;

            // Update current time based on speed
            // Assuming deltaTime is in ms, and race time is in seconds
            // We need to advance currentTime by (deltaTime / 1000) * playbackSpeed

            if (isPlaying) {
                setCurrentTime((prev) => {
                    const nextTime = prev + (deltaTime / 1000) * playbackSpeed;
                    return nextTime > duration ? duration : nextTime; // Stop at end
                });
            }
        }
        previousTimeRef.current = time;
        requestRef.current = requestAnimationFrame(animate);
    };

    useEffect(() => {
        requestRef.current = requestAnimationFrame(animate);
        return () => cancelAnimationFrame(requestRef.current);
    }, [isPlaying, playbackSpeed, duration]); // Re-bind if these change

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    return (
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 flex flex-col gap-3">
            {/* Time Display */}
            <div className="flex justify-between text-sm font-mono text-blue-400">
                <span>{formatTime(currentTime)}</span>
                <span>{formatTime(duration)}</span>
            </div>

            {/* Slider with Lap Markers */}
            <div className="relative w-full h-6">
                {/* Lap Markers */}
                {/* This would ideally come from raceData/telemetryData */}
                <div className="absolute top-0 left-0 w-full h-full pointer-events-none">
                    {/* Placeholder for lap markers - in real implementation, map lap start times to positions */}
                </div>

                <input
                    type="range"
                    min="0"
                    max={duration || 100}
                    value={currentTime}
                    onChange={(e) => setCurrentTime(parseFloat(e.target.value))}
                    className="absolute top-2 w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500 z-10"
                />
            </div>

            {/* Controls */}
            <div className="flex items-center justify-between mt-1">
                <button
                    onClick={() => setIsPlaying(!isPlaying)}
                    className={`
            px-4 py-2 rounded font-bold text-sm transition-colors
            ${isPlaying ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30' : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'}
          `}
                >
                    {isPlaying ? 'PAUSE' : 'PLAY'}
                </button>

                <div className="flex gap-1">
                    {[1, 2, 4, 10].map((speed) => (
                        <button
                            key={speed}
                            onClick={() => setPlaybackSpeed(speed)}
                            className={`
                px-2 py-1 rounded text-xs font-mono transition-colors
                ${playbackSpeed === speed ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-400 hover:bg-gray-600'}
              `}
                        >
                            {speed}x
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}
