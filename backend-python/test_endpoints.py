"""
Quick test script to verify the replay endpoints are accessible
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_replay_tracks():
    """Test GET /replay/tracks"""
    print("\n" + "="*60)
    print("Testing GET /replay/tracks")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/replay/tracks")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_replay_build():
    """Test POST /replay/build"""
    print("\n" + "="*60)
    print("Testing POST /replay/build")
    print("="*60)
    
    payload = {
        "track_id": "barber",
        "race_id": "R1"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/replay/build",
            json=payload
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)[:500]}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_tracks_available():
    """Test GET /tracks/available (existing endpoint)"""
    print("\n" + "="*60)
    print("Testing GET /tracks/available (existing endpoint)")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/tracks/available")
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Tracks found: {len(data.get('tracks', []))}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("REPLAY ENDPOINT TEST SUITE")
    print("="*60)
    
    # Test existing endpoint first
    test_tracks_available()
    
    # Test new endpoints
    test_replay_tracks()
    test_replay_build()
    
    print("\n" + "="*60)
    print("Tests Complete")
    print("="*60 + "\n")
