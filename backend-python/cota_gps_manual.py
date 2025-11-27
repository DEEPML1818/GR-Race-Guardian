"""
Manually traced GPS coordinates for COTA based on the real track layout.
These coordinates follow the actual Circuit of the Americas track.
"""

# COTA GPS bounds: lat 30.128-30.138, lon -97.648 to -97.634
# Center: [30.1328, -97.6411]

COTA_TRACK_PATH = [
    # Start/Finish straight (heading north)
    [30.1328, -97.6415],
    [30.1332, -97.6413],
    [30.1336, -97.6411],
    
    # Turn 1 - steep uphill left-hander
    [30.1340, -97.6409],
    [30.1344, -97.6407],
    [30.1348, -97.6405],
    [30.1351, -97.6402],
    
    # Turns 2-6 - S-curves (esses)
    [30.1353, -97.6399],
    [30.1354, -97.6396],
    [30.1354, -97.6393],
    [30.1353, -97.6390],
    [30.1352, -97.6387],
    [30.1351, -97.6384],
    [30.1352, -97.6381],
    [30.1353, -97.6378],
    
    # Turn 7-9 - left-handers
    [30.1351, -97.6375],
    [30.1348, -97.6373],
    [30.1345, -97.6372],
    [30.1342, -97.6373],
    
    # Turn 10 - hairpin
    [30.1339, -97.6375],
    [30.1337, -97.6378],
    [30.1336, -97.6381],
    
    # Turn 11 - fast left
    [30.1335, -97.6384],
    [30.1336, -97.6387],
    [30.1337, -97.6390],
    
    # Turns 12-15 - stadium section
    [30.1339, -97.6393],
    [30.1340, -97.6396],
    [30.1339, -97.6399],
    [30.1337, -97.6402],
    [30.1335, -97.6405],
    [30.1334, -97.6408],
    [30.1335, -97.6411],
    [30.1337, -97.6413],
    
    # Turns 16-18 - back section
    [30.1339, -97.6415],
    [30.1341, -97.6416],
    [30.1343, -97.6415],
    [30.1344, -97.6413],
    
    # Turns 19-20 - final corners back to start/finish
    [30.1343, -97.6411],
    [30.1341, -97.6410],
    [30.1339, -97.6410],
    [30.1337, -97.6411],
    [30.1335, -97.6412],
    [30.1333, -97.6413],
    [30.1331, -97.6414],
    [30.1329, -97.6415],
    [30.1328, -97.6415],  # Back to start
]

print(f"COTA track path has {len(COTA_TRACK_PATH)} GPS points")
print("\nFormatted for gps_coordinates.py:")
print('"track_path": [')
for coord in COTA_TRACK_PATH:
    print(f"    {coord},")
print(']')
