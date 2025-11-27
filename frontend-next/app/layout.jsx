import '../styles/globals.css';

export const metadata = {
    title: 'GR Race Guardian - Track Replay',
    description: 'Interactive track replay system for GR Race Guardian',
};

export default function RootLayout({ children }) {
    return (
        <html lang="en">
            <body className="bg-gray-900 text-white min-h-screen">
                {children}
            </body>
        </html>
    );
}
