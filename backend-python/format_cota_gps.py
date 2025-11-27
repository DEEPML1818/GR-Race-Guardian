"""
Update gps_coordinates.py with real COTA GPS data from OpenStreetMap
"""

import json

# Load the extracted GPS data
with open('real_track_gps_coordinates.json', 'r') as f:
    gps_data = json.load(f)

# Get COTA coordinates
cota_coords = gps_data['cota']['track_path']

print(f"COTA has {len(cota_coords)} GPS points")
print("\nAdd this to gps_coordinates.py under the 'cota' entry:")
print('\n"track_path": [')
for coord in cota_coords:
    print(f"    [{coord[0]}, {coord[1]}],")
print(']')
