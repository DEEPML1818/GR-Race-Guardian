"""
Test Script for Race Replay Builder

Tests the replay builder with actual CSV data from Barber Motorsports Park.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from grracing.race_replay_builder import RaceReplayBuilder
import json

def test_barber_race1():
    """Test with Barber Race 1 data"""
    print("=" * 60)
    print("Testing Race Replay Builder - Barber Race 1")
    print("=" * 60)
    
    # Initialize builder
    builder = RaceReplayBuilder("barber")
    
    # File paths
    base_path = "barber-motorsports-park/barber"
    results_csv = f"{base_path}/03_Provisional Results_Race 1_Anonymized.CSV"
    lap_times_csv = f"{base_path}/R1_barber_lap_time.csv"
    
    # Check files exist
    if not os.path.exists(results_csv):
        print(f"❌ Results CSV not found: {results_csv}")
        return False
    
    if not os.path.exists(lap_times_csv):
        print(f"❌ Lap times CSV not found: {lap_times_csv}")
        return False
    
    print(f"✅ Found results CSV: {results_csv}")
    print(f"✅ Found lap times CSV: {lap_times_csv}")
    print()
    
    # Build replay
    try:
        print("Building replay...")
        replay_data = builder.build_replay_json(
            results_csv,
            lap_times_csv,
            output_path="test_barber_race1_replay.json"
        )
        
        print("✅ Replay built successfully!")
        print()
        print("=" * 60)
        print("REPLAY SUMMARY")
        print("=" * 60)
        print(f"Track: {replay_data['track_name']}")
        print(f"Length: {replay_data['track_length_miles']} miles")
        print(f"Turns: {replay_data['turns']}")
        print(f"Total Laps: {replay_data['laps']}")
        print(f"Drivers: {len(replay_data['drivers'])}")
        print()
        
        # Show first lap
        if replay_data['replay']:
            first_lap = replay_data['replay'][0]
            print("=" * 60)
            print(f"LAP {first_lap['lap']} DETAILS")
            print("=" * 60)
            print(f"Events: {', '.join(first_lap['events']) if first_lap['events'] else 'None'}")
            print()
            print("Positions:")
            for pos in first_lap['positions'][:5]:  # Show top 5
                print(f"  P{pos['position']}: {pos['driver']} (Gap: +{pos['gap']:.3f}s, Laps: {pos['laps_completed']})")
            print()
        
        # Show overtakes
        overtakes_count = sum(1 for lap in replay_data['replay'] for event in lap['events'] if '→' in event)
        print(f"Total Overtakes Detected: {overtakes_count}")
        
        # Show sample overtakes
        print()
        print("Sample Overtakes:")
        count = 0
        for lap in replay_data['replay']:
            for event in lap['events']:
                if '→' in event:
                    print(f"  Lap {lap['lap']}: {event}")
                    count += 1
                    if count >= 5:
                        break
            if count >= 5:
                break
        
        print()
        print("=" * 60)
        print(f"✅ Replay data saved to: test_barber_race1_replay.json")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error building replay: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n")
    print("=" * 60)
    print("RACE REPLAY BUILDER TEST SUITE")
    print("=" * 60)
    print("\n")
    
    # Test Barber Race 1
    success = test_barber_race1()
    
    print("\n")
    if success:
        print("✓ ALL TESTS PASSED!")
    else:
        print("✗ TESTS FAILED")
    print("\n")


if __name__ == "__main__":
    main()
