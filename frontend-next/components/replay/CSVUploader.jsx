'use client';

import { useState, useRef } from 'react';
import { useParams } from 'next/navigation';
import useRaceReplay from '../../hooks/useRaceReplay';
import { parseCSV } from '../../utils/replayUtils';

export default function CSVUploader() {
    const params = useParams();
    const trackId = params?.track || 'barber';
    const { setRaceData, setTelemetryData } = useRaceReplay();
    const [isDragging, setIsDragging] = useState(false);
    const [fileName, setFileName] = useState(null);
    const [parsing, setParsing] = useState(false);
    const [dataInfo, setDataInfo] = useState(null);
    const fileInputRef = useRef(null);

    const detectCSVType = (data) => {
        if (!data || data.length === 0) return 'unknown';

        const firstRow = data[0];
        const columns = Object.keys(firstRow);

        // Check if it's telemetry data (has telemetry_name column)
        if (columns.includes('telemetry_name') && columns.includes('telemetry_value')) {
            return 'telemetry';
        }

        // Check if it's lap timing data
        if (columns.includes('lap') && columns.includes('vehicle_number') && columns.includes('timestamp')) {
            return 'lap_times';
        }

        // Check if it's race results
        if (columns.includes('POSITION') || columns.includes('DRIVER')) {
            return 'results';
        }

        return 'unknown';
    };

    const fetchGPSReplayData = async (trackId, csvType, file = null) => {
        try {
            let response;

            if (file) {
                // Upload CSV for processing
                const formData = new FormData();
                formData.append('file', file);

                response = await fetch(`http://127.0.0.1:8000/replay/telemetry/${trackId}`, {
                    method: 'POST',
                    body: formData
                });
            } else {
                // Fetch pre-loaded data
                response = await fetch(`http://127.0.0.1:8000/replay/telemetry/${trackId}`);
            }

            if (response.ok) {
                const replayData = await response.json();

                // Check if we got a valid replay structure
                if (replayData.frames && replayData.frames.length > 0) {
                    setTelemetryData(replayData);
                    return true;
                }
            }
        } catch (err) {
            console.error('Failed to fetch GPS replay data:', err);
        }
        return false;
    };

    const handleFile = async (file) => {
        if (!file) return;

        if (file.type !== 'text/csv' && !file.name.endsWith('.csv')) {
            alert('Please upload a CSV file');
            return;
        }

        setFileName(file.name);
        setParsing(true);

        try {
            const data = await parseCSV(file);
            console.log("Parsed CSV Data:", data.length, "rows");

            const csvType = detectCSVType(data);
            console.log("Detected CSV type:", csvType);

            // Set basic race data
            setRaceData(data);

            // Try to fetch GPS replay data if it's lap timing data
            if (csvType === 'lap_times') {
                const hasGPS = await fetchGPSReplayData(trackId, csvType, file);

                setDataInfo({
                    type: csvType,
                    rows: data.length,
                    hasGPS: hasGPS,
                    vehicles: [...new Set(data.map(r => r.vehicle_number))].length
                });
            } else {
                setDataInfo({
                    type: csvType,
                    rows: data.length,
                    hasGPS: false
                });
            }

        } catch (err) {
            console.error("CSV Parse Error:", err);
            alert('Failed to parse CSV');
        } finally {
            setParsing(false);
        }
    };

    const onDragOver = (e) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const onDragLeave = (e) => {
        e.preventDefault();
        setIsDragging(false);
    };

    const onDrop = (e) => {
        e.preventDefault();
        setIsDragging(false);
        const file = e.dataTransfer.files[0];
        handleFile(file);
    };

    return (
        <div
            className={`
        border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors
        ${isDragging ? 'border-blue-500 bg-blue-500/10' : 'border-gray-700 hover:border-gray-600'}
      `}
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
            onClick={() => fileInputRef.current?.click()}
        >
            <input
                type="file"
                ref={fileInputRef}
                className="hidden"
                accept=".csv"
                onChange={(e) => handleFile(e.target.files[0])}
            />

            {parsing ? (
                <div className="text-blue-400 text-sm">Parsing CSV...</div>
            ) : fileName ? (
                <div className="text-green-400 text-sm">
                    <div className="font-medium mb-2">✓ Loaded: {fileName}</div>
                    {dataInfo && (
                        <div className="text-xs text-gray-400 space-y-1">
                            <div>Type: {dataInfo.type}</div>
                            <div>Rows: {dataInfo.rows}</div>
                            {dataInfo.vehicles && <div>Vehicles: {dataInfo.vehicles}</div>}
                            {dataInfo.hasGPS && (
                                <div className="text-blue-400 font-medium">
                                    🗺️ GPS Track Data Loaded
                                </div>
                            )}
                        </div>
                    )}
                </div>
            ) : (
                <div className="text-gray-400 text-sm">
                    <span className="block mb-1 text-2xl">📄</span>
                    Click or Drag CSV here
                    <div className="text-xs mt-2 text-gray-500">
                        Supports: Lap Times, Telemetry, Results
                    </div>
                </div>
            )}
        </div>
    );
}
