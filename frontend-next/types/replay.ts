/**
 * Track Replay Data Schemas
 * 
 * TypeScript interfaces for race replay visualization data structures.
 */

export interface TrackInfo {
    id: string;
    name: string;
    length_miles: number;
    turns: number;
    sectors: number;
}

export interface DriverPosition {
    driver: string;
    vehicle_number: number;
    position: number;
    gap: number; // seconds behind leader
    laps_completed: number;
}

export interface LapEvent {
    type: 'race_start' | 'overtake' | 'pit_stop' | 'dnf' | 'safety_car' | 'yellow_flag';
    description: string;
    driver?: string;
    lap?: number;
}

export interface LapData {
    lap: number;
    positions: DriverPosition[];
    events: string[];
    timestamp?: string;
}

export interface RaceReplayData {
    track: string;
    track_name: string;
    track_length_miles: number;
    turns: number;
    laps: number;
    drivers: string[];
    replay: LapData[];
}

export interface ReplayBuildRequest {
    track_id: string;
    race_id: string;
}

export interface ReplayBuildResponse {
    success: boolean;
    track: string;
    track_name: string;
    track_length_miles: number;
    turns: number;
    laps: number;
    drivers: string[];
    replay: LapData[];
    error?: string;
}

export interface TrackCoordinate {
    x: number;
    y: number;
    type: 'start_finish' | 'turn' | 'straight';
    name?: string;
}

export interface TrackMapData {
    track_id: string;
    coordinates: TrackCoordinate[];
    svg_path: string;
}

export interface ReplayState {
    currentLap: number;
    isPlaying: boolean;
    playbackSpeed: number;
    selectedTrack: string | null;
    selectedRace: string | null;
}

export interface RaceResultRow {
    POSITION: number;
    NUMBER: number;
    STATUS: string;
    LAPS: number;
    TOTAL_TIME: string;
    GAP_FIRST: string;
    GAP_PREVIOUS: string;
    FL_LAPNUM: number;
    FL_TIME: string;
    FL_KPH: number;
    DRIVER?: string;
}

export interface LapTimeRow {
    lap: number;
    vehicle_number: number;
    timestamp: string;
    vehicle_id: string;
    meta_event?: string;
    meta_session?: string;
}

export interface LapAnomaly {
    vehicle_number: number;
    lap: number;
    type: 'slow_lap' | 'pit_stop' | 'safety_car' | 'yellow_flag';
    expected_time?: number;
    actual_time?: number;
    deviation?: number;
}

export interface Overtake {
    lap: number;
    overtaking_driver: string;
    overtaken_driver: string;
    new_position: number;
    positions_gained: number;
}

export interface SectorTime {
    driver: string;
    lap: number;
    sector: number;
    time: number;
    speed?: number;
}

export interface PitStop {
    driver: string;
    lap: number;
    pit_in_time: string;
    pit_out_time: string;
    pit_duration: number;
    position_before: number;
    position_after: number;
}

export interface RaceStatistics {
    total_overtakes: number;
    total_pit_stops: number;
    safety_car_laps: number[];
    fastest_lap: {
        driver: string;
        lap: number;
        time: number;
    };
    average_lap_time: number;
    race_winner: string;
    podium: string[];
}
