'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';

// Components will be imported here
import TrackMap from '../../../components/replay/TrackMap';
import ReplayController from '../../../components/replay/ReplayController';
import CSVUploader from '../../../components/replay/CSVUploader';

export default function TrackReplayPage() {
    const params = useParams();
    const trackId = params.track;

    return (
        <div className="flex flex-col h-screen bg-gray-950 text-white overflow-hidden">
            {/* Header */}
            <header className="h-14 bg-gray-900 border-b border-gray-800 flex items-center px-6 justify-between z-10">
                <div className="flex items-center gap-4">
                    <Link href="/" className="text-gray-400 hover:text-white transition-colors">
                        ← Back
                    </Link>
                    <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                        Track Replay: <span className="uppercase text-white">{trackId}</span>
                    </h1>
                </div>
                <div className="flex items-center gap-4">
                    <div className="text-sm text-gray-400">
                        GR Race Guardian Replay System
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="flex-1 relative flex">
                {/* Left Panel: Controls & Info */}
                <div className="w-80 bg-gray-900/90 backdrop-blur-md border-r border-gray-800 p-4 flex flex-col gap-6 z-10">
                    {/* Track Info */}
                    <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                        <h2 className="text-sm font-semibold text-gray-300 mb-2">Session Info</h2>
                        <div className="space-y-2 text-xs text-gray-400">
                            <div className="flex justify-between">
                                <span>Track:</span>
                                <span className="text-white capitalize">{trackId}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>Status:</span>
                                <span className="text-green-400">Ready</span>
                            </div>
                        </div>
                    </div>

                    {/* Upload Section */}
                    <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700 border-dashed">
                        <p className="text-center text-sm text-gray-400 mb-2">Upload Race Data (CSV)</p>
                        <CSVUploader />
                    </div>

                    {/* Replay Controls Placeholder */}
                    <div className="mt-auto">
                        <ReplayController />
                    </div>
                </div>

                {/* Right Panel: Map */}
                <div className="flex-1 relative bg-black">
                    <TrackMap trackId={trackId} />
                </div>
            </main>
        </div>
    );
}
