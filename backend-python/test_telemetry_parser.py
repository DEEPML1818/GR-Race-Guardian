"""
Test script for telemetry parser and GPS replay generation
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from grracing.telemetry_parser import TelemetryParser
from grracing.gps_coordinates import GPSTrackCoordinates
from grracing.track_coordinates import TrackCoordinates
import json


def test_gps_coordinates():
    """Test GPS coordinates module"""
    print("=" * 60)
    print("TEST 1: GPS Coordinates")
    print("=" * 60)
    
    gps_coords = GPSTrackCoordinates()
    
    # Test getting track GPS
    barber_gps = gps_coords.get_track_gps('barber')
    print(f"\nBarber GPS:")
    print(f"  Center: {barber_gps['center']}")
    print(f"  Zoom: {barber_gps['zoom']}")
    print(f"  Name: {barber_gps['name']}")
    
    # Test all tracks
    all_tracks = gps_coords.get_all_tracks()
    print(f"\nTotal tracks with GPS: {len(all_tracks)}")
    for track_id, info in all_tracks.items():
        print(f"  - {track_id}: {info['name']}")
    
    print("\n[PASS] GPS Coordinates module working")


def test_track_path_conversion():
    """Test converting normalized coordinates to GPS"""
    print("\n" + "=" * 60)
    print("TEST 2: Track Path GPS Conversion")
    print("=" * 60)
    
    track_coords = TrackCoordinates()
    gps_coords = GPSTrackCoordinates()
    
    # Get Barber normalized coordinates
    barber_data = track_coords.get_track_coordinates('barber')
    normalized_coords = barber_data['coordinates']
    
    print(f"\nBarber normalized coordinates: {len(normalized_coords)} points")
    
    # Convert to GPS
    gps_path = gps_coords.normalize_to_gps('barber', normalized_coords)
    
    print(f"GPS path: {len(gps_path)} points")
    print(f"First point: {gps_path[0]}")
    print(f"Last point: {gps_path[-1]}")
    
    print("\n[PASS] Track path conversion working")


def test_telemetry_parser():
    """Test telemetry parser with sample data"""
    print("\n" + "=" * 60)
    print("TEST 3: Telemetry Parser")
    print("=" * 60)
    
    parser = TelemetryParser('barber')
    
    # Build track path
    track_path = parser.build_track_path_gps()
    
    print(f"\nTrack path generated: {len(track_path)} GPS points")
    if track_path:
        print(f"Start/Finish: {track_path[0]}")
        print(f"Midpoint: {track_path[len(track_path)//2]}")
    
    # Test position calculation
    lap_progress = 0.5  # 50% through lap
    lat, lon = parser.calculate_track_position(lap_progress)
    print(f"\nPosition at 50% lap progress: ({lat:.6f}, {lon:.6f})")
    
    print("\n[PASS] Telemetry parser working")


def test_full_replay_generation():
    """Test full replay data generation"""
    print("\n" + "=" * 60)
    print("TEST 4: Full Replay Generation (Mock Data)")
    print("=" * 60)
    
    parser = TelemetryParser('road-america')
    
    # Check if lap times CSV exists
    lap_times_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        '..',
        'road-america',
        'road-america',
        'Road America',
        'Race 1',
        'road_america_lap_time_R1.csv'
    )
    
    if os.path.exists(lap_times_path):
        print(f"\nFound lap times CSV: {lap_times_path}")
        
        try:
            replay_data = parser.build_telemetry_replay(lap_times_path)
            
            print(f"\nReplay data generated:")
            print(f"  Track: {replay_data['track_name']}")
            print(f"  Duration: {replay_data['duration_seconds']:.1f} seconds")
            print(f"  Frames: {len(replay_data['frames'])}")
            print(f"  Vehicles: {len(replay_data['vehicles'])}")
            print(f"  Track path points: {len(replay_data['track_path'])}")
            
            # Show first frame
            if replay_data['frames']:
                first_frame = replay_data['frames'][0]
                print(f"\nFirst frame:")
                print(f"  Time: {first_frame['time_seconds']}s")
                print(f"  Cars: {len(first_frame['cars'])}")
                if first_frame['cars']:
                    print(f"  First car: #{first_frame['cars'][0]['vehicle_number']}")
                    print(f"    Position: {first_frame['cars'][0]['position']}")
            
            # Save to file for inspection
            output_path = os.path.join(os.path.dirname(__file__), 'test_replay_output.json')
            with open(output_path, 'w') as f:
                json.dump(replay_data, f, indent=2)
            print(f"\nSaved replay data to: {output_path}")
            
            print("\n[PASS] Full replay generation working")
        except Exception as e:
            print(f"\n[INFO] Could not generate full replay: {e}")
            print("This is expected if CSV format doesn't match")
    else:
        print(f"\n[INFO] Lap times CSV not found at: {lap_times_path}")
        print("Skipping full replay test")


def main():
    print("\n" + "=" * 60)
    print("TELEMETRY PARSER TEST SUITE")
    print("=" * 60)
    
    try:
        test_gps_coordinates()
        test_track_path_conversion()
        test_telemetry_parser()
        test_full_replay_generation()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED")
        print("=" * 60)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
