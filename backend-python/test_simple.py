"""
Test Script for Race Replay Builder - Simple Version
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from grracing.race_replay_builder import RaceReplayBuilder

def test_barber():
    print("\n" + "="*60)
    print("Testing Race Replay Builder - Barber Race 1")
    print("="*60 + "\n")
    
    builder = RaceReplayBuilder("barber")
    
    base_path = "barber-motorsports-park/barber"
    results_csv = f"{base_path}/03_Provisional Results_Race 1_Anonymized.CSV"
    lap_times_csv = f"{base_path}/R1_barber_lap_time.csv"
    
    print(f"Results CSV: {results_csv}")
    print(f"Lap times CSV: {lap_times_csv}\n")
    
    try:
        replay_data = builder.build_replay_json(
            results_csv,
            lap_times_csv,
            output_path="test_barber_replay.json"
        )
        
        print("SUCCESS! Replay built.\n")
        print(f"Track: {replay_data['track_name']}")
        print(f"Laps: {replay_data['laps']}")
        print(f"Drivers: {len(replay_data['drivers'])}")
        print(f"\nOutput saved to: test_barber_replay.json\n")
        
        return True
    except Exception as e:
        print(f"ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_barber()
