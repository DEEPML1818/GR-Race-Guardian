import Link from 'next/link';

const tracks = [
    { id: 'barber', name: 'Barber Motorsports Park', location: 'Birmingham, AL' },
    { id: 'cota', name: 'Circuit of the Americas', location: 'Austin, TX' },
    { id: 'indianapolis', name: 'Indianapolis Motor Speedway', location: 'Indianapolis, IN' },
    { id: 'road-america', name: 'Road America', location: 'Elkhart Lake, WI' },
    { id: 'sebring', name: 'Sebring International Raceway', location: 'Sebring, FL' },
    { id: 'sonoma', name: 'Sonoma Raceway', location: 'Sonoma, CA' },
    { id: 'vir', name: 'Virginia International Raceway', location: 'Alton, VA' },
];

export default function TrackSelectorPage() {
    return (
        <div className="min-h-screen bg-gray-950 text-white p-8">
            <div className="max-w-4xl mx-auto">
                <h1 className="text-3xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                    Select a Track
                </h1>
                <p className="text-gray-400 mb-8">Choose a circuit to launch the replay system.</p>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {tracks.map((track) => (
                        <Link
                            key={track.id}
                            href={`/replay/${track.id}`}
                            className="block group"
                        >
                            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 hover:border-blue-500/50 hover:bg-gray-800 transition-all duration-300 relative overflow-hidden">
                                <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                                    <svg width="100" height="100" viewBox="0 0 24 24" fill="currentColor">
                                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9V8h2v8zm4 0h-2V8h2v8z" />
                                    </svg>
                                </div>

                                <h3 className="text-xl font-bold text-white mb-1 group-hover:text-blue-400 transition-colors">
                                    {track.name}
                                </h3>
                                <p className="text-sm text-gray-500">
                                    {track.location}
                                </p>

                                <div className="mt-4 flex items-center text-blue-500 text-sm font-medium opacity-0 group-hover:opacity-100 transform translate-y-2 group-hover:translate-y-0 transition-all">
                                    Launch Replay →
                                </div>
                            </div>
                        </Link>
                    ))}
                </div>
            </div>
        </div>
    );
}
