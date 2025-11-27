"""
Generate sample GPS replay data for COTA track.
This creates a mock replay with cars moving around the track.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from grracing.telemetry_parser import TelemetryParser
import json
import pandas as pd
from datetime import datetime, timedelta

# Create sample lap times data
track_id = "cota"
parser = TelemetryParser(track_id)

# Generate sample data: 5 cars, 3 laps each
vehicles = [1, 2, 3, 4, 5]
start_time = datetime(2024, 1, 1, 12, 0, 0)

data = []
for vehicle in vehicles:
    lap_time_base = 120 + vehicle * 2  # Each car slightly slower
    current_time = start_time + timedelta(seconds=vehicle * 5)  # Stagger starts
    
    for lap in range(1, 4):
        # Create multiple points per lap for smooth animation
        lap_time = lap_time_base + (lap - 1) * 0.5  # Slight degradation
        points_per_lap = 20
        
        for i in range(points_per_lap):
            progress = i / points_per_lap
            time_offset = lap_time * progress
            
            data.append({
                'timestamp': current_time + timedelta(seconds=time_offset),
                'vehicle_number': vehicle,
                'lap': lap,
                'lap_progress': progress
            })
        
        current_time += timedelta(seconds=lap_time)

# Create DataFrame and save to CSV
df = pd.DataFrame(data)
csv_path = "sample_cota_lap_times.csv"
df.to_csv(csv_path, index=False)

print(f"Created sample CSV: {csv_path}")

# Build replay data
replay_data = parser.build_telemetry_replay(csv_path)

# Save to JSON
output_path = "mock_gps_replay_cota.json"
with open(output_path, 'w') as f:
    json.dump(replay_data, f, indent=2)

print(f"Created GPS replay data: {output_path}")
print(f"Track: {replay_data['track_name']}")
print(f"Vehicles: {len(replay_data['vehicles'])}")
print(f"Frames: {len(replay_data['frames'])}")
print(f"Duration: {replay_data['duration_seconds']:.1f}s")

# Clean up CSV
os.remove(csv_path)
print(f"Cleaned up {csv_path}")
