"""
Comprehensive test for the replay endpoint after numpy fix
Tests both the endpoint availability and data correctness
"""
import requests
import json

def test_endpoint_exists():
    """Test if the endpoint is registered"""
    print("=" * 60)
    print("TEST 1: Endpoint Registration")
    print("=" * 60)
    
    try:
        # Try to access the endpoint with invalid data to see if it exists
        response = requests.post("http://127.0.0.1:8000/replay/build", json={})
        
        if response.status_code == 404:
            print("[FAIL] Endpoint not found (404)")
            print("   -> The server needs to be restarted!")
            return False
        else:
            print("[PASS] Endpoint exists")
            return True
    except Exception as e:
        print(f"[ERROR] Cannot connect to server - {e}")
        return False

def test_replay_build():
    """Test the actual replay building"""
    print("\n" + "=" * 60)
    print("TEST 2: Replay Build Functionality")
    print("=" * 60)
    
    url = "http://127.0.0.1:8000/replay/build"
    payload = {
        "track_id": "barber",
        "race_id": "race-1"
    }
    
    print(f"\nRequest: POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            print("[PASS] Request successful")
            
            data = response.json()
            
            # Validate response structure
            print("\n" + "-" * 60)
            print("Response Data Validation:")
            print("-" * 60)
            
            checks = [
                ("success", data.get("success") == True),
                ("track", "track" in data),
                ("track_name", "track_name" in data),
                ("laps", "laps" in data and isinstance(data.get("laps"), int)),
                ("drivers", "drivers" in data and isinstance(data.get("drivers"), list)),
                ("replay", "replay" in data and isinstance(data.get("replay"), list)),
            ]
            
            all_passed = True
            for check_name, passed in checks:
                status = "[PASS]" if passed else "[FAIL]"
                print(f"  {status} {check_name}: {passed}")
                if not passed:
                    all_passed = False
            
            if all_passed:
                print("\n" + "=" * 60)
                print("REPLAY DATA SUMMARY")
                print("=" * 60)
                print(f"  Track: {data.get('track_name')}")
                print(f"  Track ID: {data.get('track')}")
                print(f"  Total Laps: {data.get('laps')}")
                print(f"  Drivers: {len(data.get('drivers', []))}")
                print(f"  Replay Entries: {len(data.get('replay', []))}")
                
                # Show first lap
                if data.get('replay'):
                    first_lap = data['replay'][0]
                    print(f"\n  First Lap:")
                    print(f"    Lap Number: {first_lap.get('lap')}")
                    print(f"    Positions: {len(first_lap.get('positions', []))}")
                    print(f"    Events: {first_lap.get('events')}")
                    
                    # Show top 3 positions
                    if first_lap.get('positions'):
                        print(f"\n  Top 3 Positions (Lap 1):")
                        for pos in first_lap['positions'][:3]:
                            print(f"    P{pos['position']}: {pos['driver']} (Gap: {pos['gap']}s)")
                
                print("\n" + "=" * 60)
                print("ALL TESTS PASSED!")
                print("=" * 60)
                return True
            else:
                print("\n[FAIL] Response structure validation failed")
                return False
                
        elif response.status_code == 500:
            print("[FAIL] Internal Server Error")
            print(f"\nError: {response.text}")
            print("\nNOTE: This might be the numpy serialization error.")
            print("   Check the server logs for details.")
            return False
        else:
            print(f"[FAIL] Unexpected status code")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("[ERROR] Request timeout (>30s)")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("GR RACE GUARDIAN - REPLAY ENDPOINT TEST SUITE")
    print("=" * 60)
    
    # Test 1: Check if endpoint exists
    endpoint_ok = test_endpoint_exists()
    
    if not endpoint_ok:
        print("\n" + "=" * 60)
        print("SERVER RESTART REQUIRED")
        print("=" * 60)
        print("\nPlease restart the backend server:")
        print("  1. Stop the current server (CTRL+C)")
        print("  2. Run: cd backend-python")
        print("  3. Run: python app.py")
        print("  4. Run this test again")
        return
    
    # Test 2: Build replay
    test_replay_build()

if __name__ == "__main__":
    main()
