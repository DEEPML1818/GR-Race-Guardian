"""
Test the new coordinates endpoint and recursive file search
"""
import requests
import json

def test_coordinates_endpoint():
    print("=" * 60)
    print("TEST: Coordinates Endpoint")
    print("=" * 60)
    
    url = "http://127.0.0.1:8000/tracks/barber/coordinates"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ PASSED: Coordinates retrieved")
            print(f"  Track: {data.get('name')}")
            print(f"  Turns: {data.get('turns')}")
            print(f"  SVG Path length: {len(data.get('svg_path', ''))}")
            return True
        else:
            print(f"❌ FAILED: {response.text}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    test_coordinates_endpoint()
