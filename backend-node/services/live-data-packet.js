/**
 * Unified Live Data Packet Generator
 * 
 * Combines all race data into a single packet delivered every second.
 */

const axios = require('axios');

const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:8000';

class LiveDataPacketGenerator {
    constructor() {
        this.cache = new Map(); // Cache for driver twins and race twins
        this.cacheTimeout = 5000; // Cache timeout: 5 seconds
    }

    /**
     * Generate unified live data packet
     * 
     * Combines:
     * - Live race data (lap times, positions, sectors)
     * - Driver Twins (behavior models)
     * - Race Twin (Monte Carlo predictions)
     * - Predictions (next lap, stint pace)
     * - Strategy (pit decisions, recommendations)
     */
    async generateLiveDataPacket(raceData) {
        const {
            timestamp,
            lap,
            drivers,
            race_id = "race_1",
            total_laps = 50
        } = raceData;

        try {
            // Parallel fetch all data sources
            const [
                driverTwins,
                raceTwin,
                predictions,
                strategy
            ] = await Promise.all([
                this._fetchDriverTwins(drivers),
                this._fetchRaceTwin(race_id, drivers, total_laps, lap),
                this._generatePredictions(drivers, lap),
                this._generateStrategy(race_id, drivers, lap)
            ]);

            // Combine into unified packet
            const unifiedPacket = {
                timestamp: timestamp || new Date().toISOString(),
                lap: lap || 1,
                race_id: race_id,
                liveData: {
                    lap_times: drivers.map(d => d.lapTime || d.lap_time),
                    positions: drivers.map(d => d.position),
                    sectors: drivers.map(d => d.sector),
                    deltas: drivers.map(d => d.deltaToLeader || d.delta || 0),
                    drivers: drivers.map(d => ({
                        id: d.id || d.driver_id,
                        position: d.position,
                        lapTime: d.lapTime || d.lap_time,
                        sector: d.sector,
                        deltaToLeader: d.deltaToLeader || d.delta || 0
                    }))
                },
                driverTwin: driverTwins,
                raceTwin: raceTwin,
                predictions: predictions,
                strategy: strategy
            };

            return unifiedPacket;
        } catch (error) {
            console.error('Error generating live data packet:', error);
            // Return minimal packet on error
            return {
                timestamp: timestamp || new Date().toISOString(),
                lap: lap || 1,
                race_id: race_id,
                liveData: {
                    lap_times: drivers?.map(d => d.lapTime) || [],
                    positions: drivers?.map(d => d.position) || [],
                    sectors: drivers?.map(d => d.sector) || [],
                    deltas: drivers?.map(d => d.deltaToLeader || 0) || []
                },
                driverTwin: {},
                raceTwin: {},
                predictions: {},
                strategy: {},
                error: error.message
            };
        }
    }

    /**
     * Fetch Driver Twins for all drivers
     */
    async _fetchDriverTwins(drivers) {
        const twins = {};

        for (const driver of drivers || []) {
            try {
                const driverId = driver.id || driver.driver_id;
                
                // Check cache first
                const cached = this._getCached(`twin_${driverId}`);
                if (cached) {
                    twins[driverId] = cached;
                    continue;
                }

                // Generate Driver Twin from driver data
                const lapTimes = driver.lap_times || [driver.lapTime].filter(Boolean);
                const sectorTimes = driver.sector_times || [
                    {
                        S1: driver.sector === 'S1' ? driver.lapTime / 3 : 31.5,
                        S2: driver.sector === 'S2' ? driver.lapTime / 3 : 32.0,
                        S3: driver.sector === 'S3' ? driver.lapTime / 3 : 31.7
                    }
                ];

                // Use update-loop endpoint for real-time recalculation each lap
                const currentLap = driver.current_lap || driver.lap || 1;
                const latestLapTime = driver.lapTime || (lapTimes.length > 0 ? lapTimes[lapTimes.length - 1] : null);
                const latestSectorTimes = sectorTimes.length > 0 ? sectorTimes[sectorTimes.length - 1] : { S1: 31.5, S2: 32.0, S3: 31.7 };
                
                if (latestLapTime) {
                    // Use update-loop endpoint which maintains history and recalculates each lap
                    const response = await axios.post(
                        `${PYTHON_API_URL}/driver-twin/update-loop`,
                        {
                            driver_id: driverId,
                            lap_time: latestLapTime,
                            sector_times: latestSectorTimes,
                            telemetry_data: driver.telemetry || null,
                            tire_compound: driver.tire_compound || 'MEDIUM',
                            current_lap: currentLap,
                            emit_to_nodejs: false  // We'll handle broadcasting ourselves
                        }
                    );

                    if (response.data.success && response.data.driver_twin) {
                        twins[driverId] = response.data.driver_twin;
                        this._setCache(`twin_${driverId}`, twins[driverId]);
                    }
                } else if (lapTimes.length > 0) {
                    // Fallback to regular update if no latest lap time
                    const response = await axios.post(
                        `${PYTHON_API_URL}/driver-twin/update`,
                        {
                            driver_id: driverId,
                            lap_times: lapTimes,
                            sector_times: sectorTimes,
                            tire_compound: driver.tire_compound || 'MEDIUM',
                            current_lap: currentLap
                        }
                    );

                    if (response.data.success && response.data.driver_twin) {
                        twins[driverId] = response.data.driver_twin;
                        this._setCache(`twin_${driverId}`, twins[driverId]);
                    }
                }
            } catch (error) {
                console.error(`Error fetching Driver Twin for ${driver.id}:`, error.message);
                // Use default twin on error
                twins[driver.id] = this._defaultDriverTwin(driver.id);
            }
        }

        return twins;
    }

    /**
     * Fetch Race Twin (Monte Carlo simulation)
     */
    async _fetchRaceTwin(raceId, drivers, totalLaps, currentLap) {
        try {
            // Check cache first
            const cached = this._getCached(`race_twin_${raceId}`);
            if (cached) {
                return cached;
            }

            // Prepare driver data for simulation
            const driverData = (drivers || []).map(driver => ({
                id: driver.id || driver.driver_id,
                position: driver.position || 1,
                lap_times: driver.lap_times || [driver.lapTime].filter(Boolean),
                sector_times: driver.sector_times || [],
                tire_age: driver.tire_age || 0,
                tire_compound: driver.tire_compound || 'MEDIUM',
                current_lap: currentLap || 1
            }));

            const response = await axios.post(
                `${PYTHON_API_URL}/race-twin/simulate`,
                {
                    race_id: raceId,
                    drivers: driverData,
                    total_laps: totalLaps || 50,
                    current_lap: currentLap || 1,
                    num_simulations: 100  // Faster simulations for real-time
                }
            );

            if (response.data.success && response.data.race_twin) {
                const raceTwin = response.data.race_twin;
                this._setCache(`race_twin_${raceId}`, raceTwin);
                return raceTwin;
            }
        } catch (error) {
            console.error('Error fetching Race Twin:', error.message);
            return this._defaultRaceTwin();
        }

        return this._defaultRaceTwin();
    }

    /**
     * Generate predictions for next lap and stint
     */
    async _generatePredictions(drivers, currentLap) {
        const predictions = {};

        for (const driver of drivers || []) {
            try {
                const driverId = driver.id || driver.driver_id;

                // Predict next lap time
                const lapPrediction = await axios.post(
                    `${PYTHON_API_URL}/predict/lap`,
                    {
                        track_temp: 28.0,
                        ambient_temp: 25.0,
                        tire_age: driver.tire_age || 10,
                        stint_number: 1,
                        fuel_load: 80.0,
                        track_condition: 'dry',
                        driver_pace_vector: 0.05,
                        driver_consistency: 0.9,
                        base_lap_time: driver.lapTime || 95.0
                    }
                );

                if (lapPrediction.data.success) {
                    predictions[driverId] = {
                        next_lap_time: lapPrediction.data.predicted_lap_time,
                        confidence: lapPrediction.data.confidence
                    };
                }
            } catch (error) {
                console.error(`Error predicting for ${driver.id}:`, error.message);
                predictions[driver.id] = {
                    next_lap_time: driver.lapTime || 95.0,
                    confidence: 0.5
                };
            }
        }

        return predictions;
    }

    /**
     * Generate strategy recommendations
     */
    async _generateStrategy(raceId, drivers, currentLap) {
        const strategy = {
            pit_recommendations: [],
            pit_decisions: {}
        };

        for (const driver of drivers || []) {
            try {
                const driverId = driver.id || driver.driver_id;

                // Get pit decision
                const pitDecision = await axios.post(
                    `${PYTHON_API_URL}/strategy/pit-decision`,
                    {
                        race_id: raceId,
                        driver_id: driverId,
                        current_lap: currentLap || 1,
                        tire_age: driver.tire_age || 10,
                        tire_compound: driver.tire_compound || 'MEDIUM',
                        position: driver.position || 1
                    }
                );

                if (pitDecision.data.success) {
                    strategy.pit_decisions[driverId] = pitDecision.data;
                }
            } catch (error) {
                console.error(`Error getting strategy for ${driver.id}:`, error.message);
                strategy.pit_decisions[driver.id] = {
                    decision: 'EXTEND_STINT',
                    confidence: 'low',
                    reasoning: ['Unable to calculate']
                };
            }
        }

        return strategy;
    }

    /**
     * Cache helpers
     */
    _getCached(key) {
        const cached = this.cache.get(key);
        if (cached && (Date.now() - cached.timestamp < this.cacheTimeout)) {
            return cached.data;
        }
        this.cache.delete(key);
        return null;
    }

    _setCache(key, data) {
        this.cache.set(key, {
            data: data,
            timestamp: Date.now()
        });
    }

    /**
     * Default fallback values
     */
    _defaultDriverTwin(driverId) {
        return {
            driver_id: driverId,
            pace_vector: 0.0,
            consistency_index: 0.7,
            aggression_score: 0.5,
            confidence: 0.5,
            note: "Default twin - insufficient data"
        };
    }

    _defaultRaceTwin() {
        return {
            expected_finishing_positions: [],
            pit_recommendations: {},
            confidence: 0.5,
            note: "Default race twin - simulation unavailable"
        };
    }
}

module.exports = new LiveDataPacketGenerator();

