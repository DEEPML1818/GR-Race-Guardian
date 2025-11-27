import Papa from 'papaparse';

/**
 * Parse CSV file using Papaparse
 * @param {File} file 
 * @returns {Promise<Array>} Parsed data
 */
export const parseCSV = (file) => {
    return new Promise((resolve, reject) => {
        Papa.parse(file, {
            header: true,
            dynamicTyping: true,
            skipEmptyLines: true,
            complete: (results) => {
                if (results.errors.length > 0) {
                    console.warn('CSV Parse Errors:', results.errors);
                }
                resolve(results.data);
            },
            error: (error) => {
                reject(error);
            }
        });
    });
};

/**
 * Interpolate car position on track based on lap progress
 * @param {Object} trackData Track coordinates and SVG path
 * @param {number} lapProgress 0.0 to 1.0
 * @returns {Object} {x, y} coordinates
 */
export const getTrackPosition = (trackData, lapProgress) => {
    if (!trackData || !trackData.coordinates) return { x: 0, y: 0 };

    const points = trackData.coordinates;
    const totalPoints = points.length;

    // Find index based on progress
    // This assumes points are evenly distributed or progress is linear along points
    // For better accuracy, we should use SVG path length, but this is a good approximation
    const index = Math.floor(lapProgress * totalPoints) % totalPoints;
    const nextIndex = (index + 1) % totalPoints;

    const p1 = points[index];
    const p2 = points[nextIndex];

    // Interpolate between p1 and p2
    const segmentProgress = (lapProgress * totalPoints) - index;

    const x = p1.x + (p2.x - p1.x) * segmentProgress;
    const y = p1.y + (p2.y - p1.y) * segmentProgress;

    return { x, y };
};
