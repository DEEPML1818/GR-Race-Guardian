"""
Generate GPS track paths for all 8 race tracks.
Uses the GPS bounds to create realistic track layouts.
"""

import json

# Track GPS data with bounds
TRACKS = {
    "barber": {
        "name": "Barber Motorsports Park",
        "center": [33.5492, -86.3789],
        "bounds": [[33.5520, -86.3820], [33.5480, -86.3760]],
        "turns": 17,
        "points": 50
    },
    "cota": {
        "name": "Circuit of the Americas", 
        "center": [30.1328, -97.6411],
        "bounds": [[30.1380, -97.6480], [30.1280, -97.6340]],
        "turns": 20,
        "points": 60
    },
    "indianapolis": {
        "name": "Indianapolis Motor Speedway",
        "center": [39.7950, -86.2350],
        "bounds": [[39.8000, -86.2400], [39.7900, -86.2300]],
        "turns": 14,
        "points": 40
    },
    "road-america": {
        "name": "Road America",
        "center": [43.8014, -87.9897],
        "bounds": [[43.8100, -88.0000], [43.7930, -87.9800]],
        "turns": 14,
        "points": 50
    },
    "sebring": {
        "name": "Sebring International Raceway",
        "center": [27.4515, -81.3485],
        "bounds": [[27.4580, -81.3550], [27.4450, -81.3420]],
        "turns": 17,
        "points": 50
    },
    "sonoma": {
        "name": "Sonoma Raceway",
        "center": [38.1614, -122.4544],
        "bounds": [[38.1650, -122.4580], [38.1580, -122.4510]],
        "turns": 12,
        "points": 40
    },
    "vir": {
        "name": "Virginia International Raceway",
        "center": [36.5875, -79.2025],
        "bounds": [[36.5950, -79.2100], [36.5800, -79.1950]],
        "turns": 17,
        "points": 50
    },
    "laguna-seca": {
        "name": "WeatherTech Raceway Laguna Seca",
        "center": [36.5847, -121.7539],
        "bounds": [[36.5880, -121.7580], [36.5810, -121.7500]],
        "turns": 11,
        "points": 40
    }
}

def generate_track_path(track_id, info):
    """
    Generate a realistic track path within the GPS bounds.
    Creates a circuit-like shape with the specified number of points.
    """
    import math
    
    bounds = info['bounds']
    lat_min, lon_min = bounds[1]
    lat_max, lon_max = bounds[0]
    center_lat, center_lon = info['center']
    
    # Calculate radius (use 70% of bounds to stay within limits)
    lat_range = (lat_max - lat_min) * 0.35
    lon_range = (lon_max - lon_min) * 0.35
    
    num_points = info['points']
    path = []
    
    # Create an oval/circuit shape
    for i in range(num_points):
        angle = (i / num_points) * 2 * math.pi
        
        # Create variation to make it look like a real track (not perfect circle)
        radius_lat = lat_range * (1 + 0.3 * math.sin(angle * 3))
        radius_lon = lon_range * (1 + 0.2 * math.cos(angle * 2))
        
        lat = center_lat + radius_lat * math.sin(angle)
        lon = center_lon + radius_lon * math.cos(angle)
        
        # Ensure within bounds
        lat = max(lat_min, min(lat_max, lat))
        lon = max(lon_min, min(lon_max, lon))
        
        path.append([round(lat, 6), round(lon, 6)])
    
    # Close the loop
    path.append(path[0])
    
    return path

# Generate all tracks
all_tracks = {}
for track_id, info in TRACKS.items():
    print(f"Generating {info['name']}...")
    path = generate_track_path(track_id, info)
    all_tracks[track_id] = {
        "name": info['name'],
        "track_path": path,
        "num_points": len(path)
    }
    print(f"  Generated {len(path)} points")

# Save to JSON
with open('all_tracks_gps.json', 'w') as f:
    json.dump(all_tracks, f, indent=2)

print(f"\nSaved all tracks to all_tracks_gps.json")

# Generate Python code for gps_coordinates.py
print("\n" + "="*60)
print("Copy this into gps_coordinates.py:")
print("="*60)

for track_id, data in all_tracks.items():
    print(f'\n"{track_id}": {{')
    print(f'    "name": "{data["name"]}",')
    print(f'    "center": {TRACKS[track_id]["center"]},')
    print(f'    "zoom": 14,')
    print(f'    "bounds": {TRACKS[track_id]["bounds"]},')
    print('    "track_path": [')
    for coord in data['track_path']:
        print(f'        {coord},')
    print('    ]')
    print('},')
