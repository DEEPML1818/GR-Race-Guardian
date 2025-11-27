"""
Generate sample GPS replay data for all tracks.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from grracing.telemetry_parser import TelemetryParser
import json
import pandas as pd
from datetime import datetime, timedelta

tracks = ["barber", "cota", "indianapolis", "road-america", "sebring", "sonoma", "vir", "laguna-seca"]

for track_id in tracks:
    print(f"\nGenerating data for {track_id}...")
    
    try:
        parser = TelemetryParser(track_id)
        
        # Generate sample data: 5 cars, 3 laps each
        vehicles = [1, 2, 3, 4, 5]
        start_time = datetime(2024, 1, 1, 12, 0, 0)
        
        data = []
        for vehicle in vehicles:
            lap_time_base = 120 + vehicle * 2
            current_time = start_time + timedelta(seconds=vehicle * 5)
            
            for lap in range(1, 4):
                lap_time = lap_time_base + (lap - 1) * 0.5
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
        csv_path = f"sample_{track_id}_lap_times.csv"
        df.to_csv(csv_path, index=False)
        
        # Build replay data
        replay_data = parser.build_telemetry_replay(csv_path)
        
        # Save to JSON
        output_path = f"mock_gps_replay_{track_id}.json"
        with open(output_path, 'w') as f:
            json.dump(replay_data, f, indent=2)
        
        print(f"  [OK] Created {output_path}")
        print(f"    Vehicles: {len(replay_data['vehicles'])}, Frames: {len(replay_data['frames'])}")
        
        # Clean up CSV
        os.remove(csv_path)
        
    except Exception as e:
        print(f"  [FAIL] Failed: {e}")

print("\nDone!")
