"""
Generate mock GPS replay data for testing OpenStreetMap component
"""

import json
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from grracing.telemetry_parser import TelemetryParser


def generate_mock_replay(track_id='barber', num_cars=5, num_laps=3):
    """
    Generate mock GPS replay data for testing.
    
    Args:
        track_id: Track identifier
        num_cars: Number of cars in the race
        num_laps: Number of laps to simulate
    """
    parser = TelemetryParser(track_id)
    
    # Build track path
    track_path_gps = parser.build_track_path_gps()
    track_gps = parser.gps_coords.get_track_gps(track_id)
    track_info = parser.track_coords.get_track_coordinates(track_id)
    
    # Generate frames
    frames = []
    start_time = datetime.now()
    time_step = 0.5  # seconds between frames
    lap_time = 90  # seconds per lap (average)
    
    total_duration = num_laps * lap_time
    current_time = 0
    
    while current_time <= total_duration:
        frame = {
            'timestamp': (start_time + timedelta(seconds=current_time)).isoformat(),
            'time_seconds': current_time,
            'cars': []
        }
        
        for car_num in range(1, num_cars + 1):
            # Offset each car slightly
            car_offset = (car_num - 1) * 5  # 5 second gap between cars
            car_time = current_time - car_offset
            
            if car_time < 0:
                continue  # Car hasn't started yet
            
            # Calculate lap and progress
            lap = int(car_time / lap_time) + 1
            lap_progress = (car_time % lap_time) / lap_time
            
            if lap > num_laps:
                lap = num_laps
                lap_progress = 1.0
            
            # Get GPS position
            lat, lon = parser.calculate_track_position(lap_progress)
            
            frame['cars'].append({
                'vehicle_number': car_num,
                'lap': lap,
                'lap_progress': lap_progress,
                'position': {
                    'lat': lat,
                    'lon': lon
                }
            })
        
        frames.append(frame)
        current_time += time_step
    
    # Build complete replay data
    replay_data = {
        'track_id': track_id,
        'track_name': track_info.get('name', 'Unknown'),
        'track_gps': track_gps,
        'track_path': [{'lat': lat, 'lon': lon} for lat, lon in track_path_gps],
        'duration_seconds': total_duration,
        'frames': frames,
        'vehicles': list(range(1, num_cars + 1))
    }
    
    return replay_data


def main():
    print("Generating mock GPS replay data...")
    
    # Generate for Barber
    replay_data = generate_mock_replay(
        track_id='barber',
        num_cars=8,
        num_laps=5
    )
    
    # Save to file
    output_path = os.path.join(
        os.path.dirname(__file__),
        'mock_gps_replay_barber.json'
    )
    
    with open(output_path, 'w') as f:
        json.dump(replay_data, f, indent=2)
    
    print(f"\n[OK] Generated mock replay data:")
    print(f"  Track: {replay_data['track_name']}")
    print(f"  Duration: {replay_data['duration_seconds']} seconds")
    print(f"  Frames: {len(replay_data['frames'])}")
    print(f"  Cars: {len(replay_data['vehicles'])}")
    print(f"  Track path points: {len(replay_data['track_path'])}")
    print(f"\n[OK] Saved to: {output_path}")
    
    # Show sample frame
    if replay_data['frames']:
        sample_frame = replay_data['frames'][len(replay_data['frames']) // 2]
        print(f"\nSample frame (mid-race):")
        print(f"  Time: {sample_frame['time_seconds']}s")
        print(f"  Cars on track: {len(sample_frame['cars'])}")
        if sample_frame['cars']:
            car = sample_frame['cars'][0]
            print(f"  Car #{car['vehicle_number']}:")
            print(f"    Lap: {car['lap']}")
            print(f"    Progress: {car['lap_progress']:.1%}")
            print(f"    GPS: ({car['position']['lat']:.6f}, {car['position']['lon']:.6f})")


if __name__ == "__main__":
    main()
